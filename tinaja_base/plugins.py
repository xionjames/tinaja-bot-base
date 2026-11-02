"""Runs Plugins: processes in any language that add Commands and listeners through docs/protocol.md"""

import asyncio
import json
import logging
import os
import shlex
import time
from collections import OrderedDict

from discord.ext import commands

from tinaja_base.channel import recent_messages

PROTOCOL = 1
HANDSHAKE_TIMEOUT = 15
SHUTDOWN_TIMEOUT = 5
MAX_BACKOFF = 30
MAX_REMEMBERED_MESSAGES = 500

log = logging.getLogger(__name__)


class PluginError(Exception):
    pass


def author_data(author):
    return {
        'id': str(author.id),
        'name': author.name,
        'display_name': author.display_name,
        'mention': author.mention,
        'bot': author.bot,
    }


def message_data(message, channel_id=None):
    if channel_id is None:
        channel_id = str(message.channel.id)
    return {
        'id': str(message.id),
        'content': message.content,
        'channel_id': channel_id,
        'author': author_data(message.author),
    }


class PluginProcess:
    """One running Plugin: JSON lines over its stdin and stdout"""

    def __init__(self, name, plugin, root):
        self.name = name
        self._plugin = plugin
        self._root = root
        self._process = None

    async def start(self, hello):
        """Start the process and do the handshake, returning its register message"""
        # The Plugin never needs the token: the host does all the talking to Discord
        env = {key: value for key, value in os.environ.items() if key != 'DISCORD_BOT_TOKEN'}
        try:
            self._process = await asyncio.create_subprocess_exec(
                *shlex.split(self._plugin.run),
                cwd=self._root / self._plugin.cwd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                env=env,
                limit=2**20,
            )
        except OSError as error:
            raise PluginError(f'plugin "{self.name}" could not start "{self._plugin.run}": {error}') from error

        await self.send(hello)
        try:
            register = await asyncio.wait_for(self.read(), HANDSHAKE_TIMEOUT)
        except TimeoutError:
            await self.stop()
            raise PluginError(f'plugin "{self.name}" did not register within {HANDSHAKE_TIMEOUT}s') from None
        if register is None:
            code = await self._process.wait()
            raise PluginError(f'plugin "{self.name}" exited with code {code} before registering; see its output above')
        if register.get('type') != 'register':
            await self.stop()
            raise PluginError(f'plugin "{self.name}" answered the hello with "{register.get("type")}", not register')
        return register

    async def send(self, message):
        if not self.running:
            log.warning('plugin "%s" is not running; dropped %s', self.name, message.get('type'))
            return
        try:
            self._process.stdin.write((json.dumps(message, ensure_ascii=False) + '\n').encode())
            await self._process.stdin.drain()
        except ConnectionError:
            log.warning('plugin "%s" closed its stdin; dropped %s', self.name, message.get('type'))

    async def read(self):
        """The next message from the Plugin, or None once it exits"""
        while line := await self._process.stdout.readline():
            if not line.strip():
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                # Usually a stray print: Plugins must log to stderr
                log.warning('plugin "%s" printed a line that is not protocol JSON: %r', self.name, line[:200])
        return None

    async def wait(self):
        return await self._process.wait()

    @property
    def running(self):
        return self._process is not None and self._process.returncode is None

    async def stop(self):
        if not self.running:
            return
        await self.send({'type': 'shutdown'})
        self._process.stdin.close()
        try:
            await asyncio.wait_for(self._process.wait(), SHUTDOWN_TIMEOUT)
        except TimeoutError:
            self._process.kill()
            await self._process.wait()


async def probe(name, plugin, root, hello):
    """Start a Plugin just long enough to see it register"""
    process = PluginProcess(name, plugin, root)
    try:
        return await process.start(hello)
    finally:
        await process.stop()


def hello_message(bot):
    return {
        'type': 'hello',
        'protocol': PROTOCOL,
        'bot': {
            'name': bot.config.name,
            'prefix': bot.config.prefix,
            'id': str(bot.user.id) if bot.user else None,
        },
    }


class PluginCog(commands.Cog):
    """Turns a Plugin's registration into Commands, forwards events to it and carries out its actions"""

    def __init__(self, bot, name, plugin):
        self.__cog_name__ = name
        self._bot = bot
        self._process = PluginProcess(name, plugin, bot.config.root)
        self._command_names = []
        self._events = set()
        self._reader = None
        self._closing = False
        self._backoff = 1
        self._started_at = 0
        # Channels and messages seen in events, so actions on them don't need a Discord API call
        self._channels = {}
        self._messages = OrderedDict()

    async def cog_load(self):
        register = await self._start()
        try:
            for spec in register.get('commands', []):
                self._bot.add_command(self._command(spec['name'], spec.get('help')))
                self._command_names.append(spec['name'])
        except Exception:
            await self.cog_unload()
            raise
        self._reader = asyncio.create_task(self._read_loop())

    async def cog_unload(self):
        self._closing = True
        for name in self._command_names:
            self._bot.remove_command(name)
        if self._reader is not None:
            self._reader.cancel()
        await self._process.stop()

    async def _start(self):
        self._started_at = time.monotonic()
        register = await self._process.start(hello_message(self._bot))
        self._events = set(register.get('events', []))
        return register

    def _command(self, name, help_text):
        async def callback(ctx, *args):
            self._remember(ctx.message, ctx.channel)
            await self._process.send(
                {
                    'type': 'command',
                    'name': name,
                    'args': list(args),
                    'channel_id': str(ctx.channel.id),
                    'author': author_data(ctx.author),
                    'message': message_data(ctx.message, str(ctx.channel.id)),
                }
            )

        return commands.Command(callback, name=name, help=help_text or None)

    @commands.Cog.listener()
    async def on_ready(self):
        await self._process.send({'type': 'ready'})

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        self._remember(message, message.channel)
        if 'message' in self._events:
            await self._process.send({'type': 'message', 'message': message_data(message)})

    @commands.Cog.listener()
    async def on_mention(self, message, text):
        if 'mention' in self._events:
            self._remember(message, message.channel)
            await self._process.send({'type': 'mention', 'message': message_data(message), 'text': text})

    async def _read_loop(self):
        while True:
            message = await self._process.read()
            if message is not None:
                await self._act(message)
            elif not self._closing:
                await self._restart()
            else:
                return

    async def _restart(self):
        code = await self._process.wait()
        # A Plugin that keeps crashing right after starting waits longer each time
        self._backoff = min(self._backoff * 2, MAX_BACKOFF) if time.monotonic() - self._started_at < 60 else 1
        log.error('plugin "%s" exited with code %s; restarting in %ss', self.qualified_name, code, self._backoff)
        await asyncio.sleep(self._backoff)
        try:
            register = await self._start()
        except PluginError as error:
            log.error('%s', error)
            return  # the loop reads None again and retries
        if sorted(c['name'] for c in register.get('commands', [])) != sorted(self._command_names):
            log.warning('plugin "%s" registered different Commands; restart the Bot to apply them', self.qualified_name)
        if self._bot.is_ready():
            await self._process.send({'type': 'ready'})

    async def _act(self, action):
        kind = action.get('type')
        try:
            if kind == 'send':
                await self._do_send(action)
            elif kind == 'react':
                channel = await self._channel(action['channel_id'])
                message = await self._message(channel, action['message_id'])
                await message.add_reaction(action['emoji'])
            elif kind == 'history':
                channel_id = action['channel_id']
                channel = await self._channel(channel_id)
                messages = await recent_messages(channel, limit=min(int(action.get('limit', 20)), 100))
                for message in messages:
                    self._remember(message, channel)
                await self._process.send(
                    {
                        'type': 'result',
                        'request_id': action.get('request_id'),
                        'messages': [message_data(m, channel_id) for m in messages],
                    }
                )
            else:
                raise PluginError(f"unknown action '{kind}'")
        except Exception as error:  # noqa: BLE001 - a bad action is reported to the Plugin, not fatal to the Bot
            log.warning('plugin "%s": %s failed: %s', self.qualified_name, kind, error)
            reply = {'type': 'error', 'error': f'{kind} failed: {error}'}
            if 'request_id' in action:
                reply['request_id'] = action['request_id']
            await self._process.send(reply)

    async def _do_send(self, action):
        channel = await self._channel(action['channel_id'])
        content = str(action['content'])
        if action.get('reply_to'):
            message = await self._message(channel, action['reply_to'])
            await message.reply(content)
        else:
            await channel.send(content)

    def _remember(self, message, channel):
        self._channels[str(channel.id)] = channel
        self._messages[str(message.id)] = message
        while len(self._messages) > MAX_REMEMBERED_MESSAGES:
            self._messages.popitem(last=False)

    async def _channel(self, channel_id):
        channel = self._channels.get(channel_id) or self._bot.get_channel(int(channel_id))
        return channel or await self._bot.fetch_channel(int(channel_id))

    async def _message(self, channel, message_id):
        return self._messages.get(message_id) or await channel.fetch_message(int(message_id))
