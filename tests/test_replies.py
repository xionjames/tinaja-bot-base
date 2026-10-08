from tinaja_base.cogs.replies import reply_commands
from tinaja_base.testing import FakeContext


async def test_reply_commands_send_their_text():
    ping, rules = reply_commands({'ping': 'pong {author}', 'rules': 'Read {prefix}glossary {not a field}'}, '!')
    assert (ping.name, rules.name) == ('ping', 'rules')

    ctx = FakeContext()
    await ping.callback(ctx)
    await rules.callback(ctx)
    assert ctx.sent == ['pong @member', 'Read !glossary {not a field}']


def test_format_reply_names_the_command():
    from tinaja_base.cogs.replies import format_reply
    from tinaja_base.testing import fake_member

    assert format_reply('{author}: no {prefix}{command}', fake_member(), '!', 'nope') == '@member: no !nope'
