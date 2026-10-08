from types import SimpleNamespace

from tinaja_base.cogs.mentions import Mentions
from tinaja_base.testing import fake_member, fake_message

ME = fake_member('bot', bot=True, id=42)


class FakeBot:
    def __init__(self, is_command=False):
        self.user = ME
        self.config = SimpleNamespace(prefix='!')
        self.events = []
        self._is_command = is_command

    async def get_context(self, message):
        return SimpleNamespace(valid=self._is_command)

    def dispatch(self, event, *args):
        self.events.append((event, *args))


async def test_dispatches_mention_without_the_mention_text():
    bot = FakeBot()
    message = fake_message('<@42> hi <@!42> there', mentions=[ME])
    await Mentions(bot).on_message(message)
    assert bot.events == [('mention', message, 'hi there')]
    assert message.replies == []


async def test_sends_fallback_reply():
    message = fake_message('<@42>', mentions=[ME])
    await Mentions(FakeBot(), reply='Hi {author}! Try {prefix}help').on_message(message)
    assert message.replies == ['Hi @member! Try !help']


async def test_ignores_commands_bots_and_other_messages():
    bot = FakeBot(is_command=True)
    await Mentions(bot).on_message(fake_message('<@42> hello', mentions=[ME]))
    assert bot.events == []

    bot = FakeBot()
    await Mentions(bot).on_message(fake_message('<@42> hi', author=fake_member('other', bot=True), mentions=[ME]))
    await Mentions(bot).on_message(fake_message('hello everyone'))
    await Mentions(bot).on_message(fake_message('<@7> hi', mentions=[fake_member('friend', id=7)]))
    assert bot.events == []
