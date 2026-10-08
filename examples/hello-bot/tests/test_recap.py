from tinaja_base.testing import FakeChannel, FakeContext, fake_member, fake_message, run_command

from cogs.recap import Recap

ANA = fake_member('ana')
LUIS = fake_member('luis')


def recap_context(*earlier, command='!recap'):
    """A channel holding the earlier messages, then the Member's !recap"""
    invoking = fake_message(command, id='recap')
    return FakeContext(channel=FakeChannel([*earlier, invoking]), message=invoking)


async def test_recaps_the_latest_member_messages():
    ctx = recap_context(
        fake_message('hola', ANA), fake_message('beep', fake_member('bot', bot=True)), fake_message('que tal', LUIS)
    )
    assert await run_command(Recap(), 'recap', ctx=ctx) == ['ana: hola\nluis: que tal']


async def test_recap_count():
    ctx = recap_context(fake_message('one', ANA), fake_message('two', LUIS), command='!recap 1')
    assert await run_command(Recap(), 'recap', 1, ctx=ctx) == ['luis: two']


async def test_empty_channel():
    assert await run_command(Recap(), 'recap', ctx=recap_context()) == ['Nothing to recap yet.']
