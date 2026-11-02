"""Run a Plugin's handlers without a Bot: what they send is recorded, history comes from a list"""

from tinaja_plugin import Message


def fake_author(name='member', id='1', bot=False):
    return {'id': id, 'name': name, 'display_name': name, 'mention': f'<@{id}>', 'bot': bot}


def fake_message(content, author=None, id='100', channel_id='10'):
    return {'id': id, 'content': content, 'channel_id': channel_id, 'author': author or fake_author()}


class FakeConnection:
    def __init__(self, history=()):
        self.actions = []  # every action the Plugin took, as protocol messages
        self._history = list(history)  # message dicts, oldest first

    def write(self, message):
        self.actions.append(message)

    def history(self, channel_id, limit):
        return [Message(data, self) for data in self._history[-limit:]]


def run_event(plugin, event, history=()):
    """Dispatch one protocol event and return the actions it caused"""
    plugin.connection = FakeConnection(history)
    plugin.dispatch(event)
    return plugin.connection.actions


def run_command(plugin, name, *args, history=(), author=None, channel_id='10'):
    """Run a Command like the Bot would, returning the text it sent (sends and replies)"""
    author = author or fake_author()
    content = ' '.join(['!' + name, *args])
    event = {
        'type': 'command',
        'name': name,
        'args': list(args),
        'channel_id': channel_id,
        'author': author,
        'message': fake_message(content, author, channel_id=channel_id),
    }
    return [action['content'] for action in run_event(plugin, event, history) if action['type'] == 'send']
