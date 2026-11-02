"""Reference SDK for the tinaja-bot-base Plugin protocol (docs/protocol.md).

Python Bots should use Cogs instead; this SDK is the model the other languages' SDKs follow, and the framework's tests
use it as a real Plugin.
"""

import json
import sys
import traceback
from collections import deque

PROTOCOL = 1


class Author:
    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name', '')
        self.display_name = data.get('display_name', self.name)
        self.mention = data.get('mention', '')
        self.bot = data.get('bot', False)


class Message:
    def __init__(self, data, connection):
        self.id = data.get('id')
        self.content = data.get('content', '')
        self.channel_id = data.get('channel_id')
        self.author = Author(data.get('author', {}))
        self._connection = connection

    def reply(self, content):
        self._connection.write({'type': 'send', 'channel_id': self.channel_id, 'content': content, 'reply_to': self.id})

    def react(self, emoji):
        self._connection.write({'type': 'react', 'channel_id': self.channel_id, 'message_id': self.id, 'emoji': emoji})


class Context:
    """What a Command handler gets: who asked, where, and the words after the Command"""

    def __init__(self, event, connection):
        self.name = event['name']
        self.args = list(event.get('args', []))
        self.channel_id = event.get('channel_id')
        self.author = Author(event.get('author', {}))
        self.message = Message(event.get('message', {}), connection)
        self._connection = connection

    def send(self, content):
        self._connection.write({'type': 'send', 'channel_id': self.channel_id, 'content': content})

    def reply(self, content):
        self.message.reply(content)

    def history(self, limit=20):
        """The channel's latest Member messages, oldest first"""
        return self._connection.history(self.channel_id, limit)


class Connection:
    """JSON lines over a pair of text streams"""

    def __init__(self, reader, writer):
        self._reader = reader
        self._writer = writer
        self._pending = deque()  # events that arrived while waiting for a result
        self._next_id = 1

    def write(self, message):
        self._writer.write(json.dumps(message, ensure_ascii=False) + '\n')
        self._writer.flush()

    def read(self):
        """The next event, or None when the host closed stdin"""
        if self._pending:
            return self._pending.popleft()
        return self._read_line()

    def history(self, channel_id, limit):
        request_id = str(self._next_id)
        self._next_id += 1
        self.write({'type': 'history', 'request_id': request_id, 'channel_id': channel_id, 'limit': limit})
        while (event := self._read_line()) is not None:
            if event.get('request_id') == request_id and event.get('type') in ('result', 'error'):
                if event['type'] == 'error':
                    raise RuntimeError(event.get('error', 'history failed'))
                return [Message(data, self) for data in event.get('messages', [])]
            self._pending.append(event)
        raise EOFError('the host closed the connection')

    def _read_line(self):
        for line in self._reader:
            if line.strip():
                return json.loads(line)
        return None


class Plugin:
    def __init__(self):
        self._commands = {}  # name -> (help, handler), in registration order
        self._message_handlers = []
        self._mention_handlers = []
        self.connection = None
        self.bot = {}  # the hello's bot info: name, prefix, id

    def command(self, name, help=''):
        """Decorator: handler(ctx) runs for every !name"""

        def register(handler):
            self._commands[name] = (help, handler)
            return handler

        return register

    def on_message(self, handler):
        """handler(message) runs for every message from a Member, Commands included"""
        self._message_handlers.append(handler)
        return handler

    def on_mention(self, handler):
        """handler(message, text) runs when the Bot is @mentioned without a Command; needs [mentions] in bot.toml"""
        self._mention_handlers.append(handler)
        return handler

    def send(self, channel_id, content):
        self.connection.write({'type': 'send', 'channel_id': channel_id, 'content': content})

    def history(self, channel_id, limit=20):
        return self.connection.history(channel_id, limit)

    def registration(self):
        handlers = {'message': self._message_handlers, 'mention': self._mention_handlers}
        return {
            'type': 'register',
            'commands': [{'name': name, 'help': help} for name, (help, _) in self._commands.items()],
            'events': sorted(name for name, registered in handlers.items() if registered),
        }

    def run(self, reader=None, writer=None):
        """Serve the host until it says shutdown or closes stdin"""
        self.connection = Connection(reader or sys.stdin, writer or sys.stdout)
        while (event := self.connection.read()) is not None:
            if event.get('type') == 'shutdown':
                return
            self.handle(event)

    def handle(self, event):
        try:
            self.dispatch(event)
        except Exception:  # noqa: BLE001 - one failing handler mustn't stop the Plugin
            traceback.print_exc(file=sys.stderr)

    def dispatch(self, event):
        """Handle one event, letting handler errors through (handle() logs them instead)"""
        kind = event.get('type')
        if kind == 'hello':
            self.bot = event.get('bot', {})
            self.connection.write(self.registration())
        elif kind == 'command' and event.get('name') in self._commands:
            self._commands[event['name']][1](Context(event, self.connection))
        elif kind == 'message':
            for handler in self._message_handlers:
                handler(Message(event.get('message', {}), self.connection))
        elif kind == 'mention':
            for handler in self._mention_handlers:
                handler(Message(event.get('message', {}), self.connection), event.get('text', ''))
        elif kind == 'error':
            print(f'tinaja: the host reported an error: {event.get("error")}', file=sys.stderr)
        # anything else (ready, future events) needs no answer
