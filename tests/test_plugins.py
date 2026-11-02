import asyncio
import sys
from pathlib import Path

import pytest
from discord.ext import commands

from tinaja_base import plugins
from tinaja_base.bot import BaseBot
from tinaja_base.config import Config, Plugin
from tinaja_base.plugins import PluginError, probe
from tinaja_base.testing import FakeChannel, FakeContext, fake_member, fake_message

# The Python SDK's reference Plugin: hello, echo, recap, replies to mentions, reacts to "ping"
REFERENCE = Plugin(run=f'"{sys.executable}" "{Path(__file__).parent.parent / "sdk/python/conformance/plugin.py"}"')

# Speaks the protocol by hand, to test what the SDK never does
RAW = """
import json, os, sys

def send(message):
    print(json.dumps(message), flush=True)

for line in sys.stdin:
    event = json.loads(line)
    if event['type'] == 'hello':
        send({'type': 'register', 'commands': [{'name': n} for n in ('dance', 'token', 'crash')], 'events': []})
    elif event['type'] == 'command':
        channel = event['channel_id']
        if event['name'] == 'dance':
            send({'type': 'dance'})
            error = json.loads(sys.stdin.readline())
            send({'type': 'send', 'channel_id': channel, 'content': error['error']})
        elif event['name'] == 'token':
            print('not json, a stray print')
            send({'type': 'send', 'channel_id': channel, 'content': os.environ.get('DISCORD_BOT_TOKEN', 'no token')})
        elif event['name'] == 'crash':
            sys.exit(1)
    elif event['type'] == 'shutdown':
        break
"""


@pytest.fixture
def raw_plugin(tmp_path):
    (tmp_path / 'raw.py').write_text(RAW)
    return Plugin(run=f'"{sys.executable}" raw.py')


async def make_bot(root, **settings):
    bot = BaseBot(Config(token='unused', root=root, **settings))
    await bot.setup_hook()
    return bot


async def until(predicate, timeout=5):
    """Plugins answer asynchronously: wait for their effect to show up"""
    async with asyncio.timeout(timeout):
        while not predicate():
            await asyncio.sleep(0.01)


async def run(bot, name, *args, ctx=None):
    ctx = ctx or FakeContext()
    await bot.get_command(name).callback(ctx, *args)
    await until(lambda: ctx.channel.sent)
    return ctx.channel.sent


async def test_plugin_commands_answer_in_the_channel(tmp_path):
    bot = await make_bot(tmp_path, plugins={'main': REFERENCE})
    assert bot.get_command('hello').help == 'Says World'
    assert await run(bot, 'hello') == ['World']
    assert await run(bot, 'echo', 'a', 'b c') == ['a b c']
    await bot.close()


async def test_plugins_read_the_channel_history(tmp_path):
    channel = FakeChannel([fake_message('hi all', fake_member('bob'), id=1), fake_message('hey', id=2)])
    bot = await make_bot(tmp_path, plugins={'main': REFERENCE})
    assert await run(bot, 'recap', '2', ctx=FakeContext(channel=channel)) == ['bob: hi all\nmember: hey']
    await bot.close()


async def test_plugins_get_mentions_and_messages(tmp_path):
    bot = await make_bot(tmp_path, plugins={'main': REFERENCE}, mentions=True)
    cog = bot.get_cog('main')
    channel = FakeChannel()
    mention = fake_message('<@42> hi there', id=5, channel=channel)
    await cog.on_mention(mention, 'hi there')
    ping = fake_message('ping', id=6, channel=channel)
    await cog.on_message(fake_message('ping', fake_member(bot=True), id=7, channel=channel))  # bots are ignored
    await cog.on_message(ping)

    await until(lambda: mention.replies and ping.reactions)
    assert mention.replies == ['You said: hi there']
    assert ping.reactions == ['🏓']
    await bot.close()


async def test_bad_actions_are_reported_to_the_plugin(tmp_path, raw_plugin):
    bot = await make_bot(tmp_path, plugins={'raw': raw_plugin})
    assert await run(bot, 'dance') == ["dance failed: unknown action 'dance'"]
    await bot.close()


async def test_plugins_never_see_the_token(tmp_path, raw_plugin, monkeypatch):
    monkeypatch.setenv('DISCORD_BOT_TOKEN', 'secret')
    bot = await make_bot(tmp_path, plugins={'raw': raw_plugin})
    assert await run(bot, 'token') == ['no token']  # and the stray print didn't break anything
    await bot.close()


async def test_a_crashed_plugin_is_restarted(tmp_path, raw_plugin, monkeypatch):
    monkeypatch.setattr(plugins, 'MAX_BACKOFF', 0.01)
    bot = await make_bot(tmp_path, plugins={'raw': raw_plugin})
    process = bot.get_cog('raw')._process._process
    await bot.get_command('crash').callback(FakeContext())
    await until(lambda: bot.get_cog('raw')._process._process is not process)
    assert await run(bot, 'token') == ['no token']
    await bot.close()


async def test_closing_the_bot_stops_the_plugin(tmp_path):
    bot = await make_bot(tmp_path, plugins={'main': REFERENCE})
    process = bot.get_cog('main')._process
    await bot.close()
    assert not process.running
    assert bot.get_command('hello') is None


async def test_a_command_name_clash_stops_the_bot(tmp_path):
    with pytest.raises(commands.CommandRegistrationError):
        await make_bot(tmp_path, replies={'hello': 'hi'}, plugins={'main': REFERENCE})


async def test_a_plugin_that_exits_early_stops_the_bot(tmp_path):
    with pytest.raises(PluginError, match='exited with code 3 before registering'):
        await make_bot(tmp_path, plugins={'main': Plugin(run=f'"{sys.executable}" -c "raise SystemExit(3)"')})


async def test_a_plugin_that_never_registers_stops_the_bot(tmp_path, monkeypatch):
    monkeypatch.setattr(plugins, 'HANDSHAKE_TIMEOUT', 0.2)
    with pytest.raises(PluginError, match='did not register'):
        await make_bot(tmp_path, plugins={'main': Plugin(run=f'"{sys.executable}" -c "import time; time.sleep(5)"')})


async def test_a_missing_executable_is_explained(tmp_path):
    with pytest.raises(PluginError, match='could not start "no-such-runtime bot.rb"'):
        await make_bot(tmp_path, plugins={'main': Plugin(run='no-such-runtime bot.rb')})


async def test_probe_returns_the_registration(tmp_path):
    hello = {'type': 'hello', 'protocol': 1, 'bot': {'name': 'Bot', 'prefix': '!', 'id': None}}
    register = await probe('main', REFERENCE, tmp_path, hello)
    assert [c['name'] for c in register['commands']] == ['hello', 'echo', 'recap']
    assert register['events'] == ['mention', 'message']
