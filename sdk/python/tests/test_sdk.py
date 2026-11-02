import sys
from pathlib import Path

import pytest
from tinaja_plugin import Plugin
from tinaja_plugin.testing import fake_author, fake_message, run_command, run_event

SDK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SDK.parent / 'conformance'))
import run as conformance


@pytest.fixture
def plugin():
    plugin = Plugin()

    @plugin.command('hello', help='Says World')
    def hello(ctx):
        ctx.send(f'World, {ctx.author.display_name}')

    @plugin.command('last')
    def last(ctx):
        ctx.reply(ctx.history(1)[0].content)

    @plugin.on_message
    def ping(message):
        message.react('🏓')

    return plugin


def test_run_command_returns_what_was_sent(plugin):
    assert run_command(plugin, 'hello', author=fake_author('jane')) == ['World, jane']


def test_history_comes_from_the_given_messages(plugin):
    assert run_command(plugin, 'last', history=[fake_message('old'), fake_message('new')]) == ['new']


def test_run_event_returns_actions(plugin):
    assert run_event(plugin, {'type': 'message', 'message': fake_message('ping', id='7')}) == [
        {'type': 'react', 'channel_id': '10', 'message_id': '7', 'emoji': '🏓'}
    ]


def test_registration_lists_commands_and_events(plugin):
    assert plugin.registration() == {
        'type': 'register',
        'commands': [{'name': 'hello', 'help': 'Says World'}, {'name': 'last', 'help': ''}],
        'events': ['message'],
    }


@pytest.mark.parametrize('fixture', sorted(conformance.FIXTURES.glob('*.jsonl')), ids=lambda path: path.stem)
def test_conformance(fixture):
    assert conformance.run_fixture(fixture, [sys.executable, str(SDK / 'conformance' / 'plugin.py')]) == []
