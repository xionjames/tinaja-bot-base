from tinaja_base.cogs.replies import reply_commands
from tinaja_base.testing import FakeContext


async def test_reply_commands_send_their_text():
    ping, rules = reply_commands({'ping': 'pong {author}', 'rules': 'Read {prefix}glossary {not a field}'}, '!')
    assert (ping.name, rules.name) == ('ping', 'rules')

    ctx = FakeContext()
    await ping.callback(ctx)
    await rules.callback(ctx)
    assert ctx.sent == ['pong @member', 'Read !glossary {not a field}']
