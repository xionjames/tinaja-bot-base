from tinaja_base.channel import recent_messages
from tinaja_base.testing import FakeChannel, fake_member, fake_message

ANA = fake_member('ana')
BOT = fake_member('bot', bot=True)


async def test_recent_messages_oldest_first_without_bots():
    channel = FakeChannel([fake_message('one', ANA), fake_message('beep', BOT), fake_message('two', ANA)])
    assert [m.content for m in await recent_messages(channel)] == ['one', 'two']


async def test_limit_keeps_the_newest():
    channel = FakeChannel([fake_message(str(n), ANA) for n in range(5)])
    assert [m.content for m in await recent_messages(channel, limit=2)] == ['3', '4']


async def test_can_include_bots():
    channel = FakeChannel([fake_message('beep', BOT)])
    assert [m.content for m in await recent_messages(channel, include_bots=True)] == ['beep']
