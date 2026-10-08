from types import SimpleNamespace

import pytest
from discord.ext import commands

from tinaja_base.bot import BaseBot
from tinaja_base.config import Config, Intents
from tinaja_base.testing import FakeContext

HELLO = """from discord.ext import commands


class Hello(commands.Cog):
    @commands.command(name='hello')
    async def hello(self, ctx):
        await ctx.send('World')
"""


@pytest.fixture
def project(tmp_path):
    (tmp_path / 'cogs').mkdir()
    (tmp_path / 'cogs' / 'hello.py').write_text(HELLO)
    (tmp_path / 'CONTEXT.md').write_text('# Bot\n\n## Language\n\n**Member**:\nA person.\n')
    return tmp_path


async def make_bot(project, **settings):
    bot = BaseBot(Config(token='unused', root=project, **settings))
    await bot.setup_hook()
    return bot


async def test_registers_builtin_reply_and_cog_commands(project):
    bot = await make_bot(project, replies={'ping': 'pong'})
    assert {'glossary', 'ping', 'hello'} <= {c.name for c in bot.commands}
    assert bot.context.lookup('member').definition == 'A person.'
    await bot.close()


async def test_mentions_cog_loads_only_when_configured(project):
    without = await make_bot(project)
    with_mentions = await make_bot(project, mentions=True)
    assert without.get_cog('Mentions') is None
    assert with_mentions.get_cog('Mentions') is not None
    await without.close()
    await with_mentions.close()


async def test_intents_follow_config(project):
    bot = await make_bot(project, intents=Intents(message_content=False, members=True))
    assert (bot.intents.message_content, bot.intents.members, bot.intents.presences) == (False, True, False)
    await bot.close()


async def test_prefix_is_plain_by_default(project):
    bot = await make_bot(project, prefix='?')
    assert bot.command_prefix == '?'
    await bot.close()


async def test_mention_works_as_prefix(project):
    bot = await make_bot(project, mention_prefix=True)
    fake_bot = SimpleNamespace(user=SimpleNamespace(id=42))
    assert bot.command_prefix(fake_bot, None) == ['<@42> ', '<@!42> ', '!']
    await bot.close()


async def test_mention_event_reaches_cog_listeners(project):
    (project / 'cogs' / 'echo.py').write_text(
        'from discord.ext import commands\n\n\nclass Echo(commands.Cog):\n    heard = []\n\n'
        '    @commands.Cog.listener()\n    async def on_mention(self, message, text):\n        self.heard.append(text)\n'
    )
    bot = await make_bot(project, mentions=True)
    # What bot.dispatch('mention', ...) calls; dispatch itself needs a logged-in event loop
    for listener in bot.extra_events['on_mention']:
        await listener(object(), 'hi there')
    assert bot.get_cog('Echo').heard == ['hi there']
    await bot.close()


def failed_command(prefix='!', name='nope'):
    ctx = FakeContext()
    ctx.prefix = prefix
    ctx.invoked_with = name
    return ctx


FALLBACK = "Sorry {author}, I don't know {prefix}{command}"


async def test_unknown_command_gets_the_fallback_reply(project):
    bot = await make_bot(project, reply_fallback=FALLBACK)
    ctx = failed_command()
    await bot.on_command_error(ctx, commands.CommandNotFound('Command "nope" is not found'))
    assert ctx.sent == ["Sorry @member, I don't know !nope"]
    await bot.close()


async def test_no_fallback_for_mentions_or_other_errors(project, monkeypatch):
    bot = await make_bot(project, reply_fallback=FALLBACK, mention_prefix=True)
    defaults = []

    async def default_handler(self, ctx, error):
        defaults.append(error)

    monkeypatch.setattr(commands.Bot, 'on_command_error', default_handler)

    # '@Bot hi there' is answered by on_mention, not as an unknown Command
    mention = failed_command(prefix='<@42> ', name='hi')
    await bot.on_command_error(mention, commands.CommandNotFound('Command "hi" is not found'))
    bad_argument = failed_command(name='recap')
    await bot.on_command_error(bad_argument, commands.BadArgument('not a number'))

    assert mention.sent == bad_argument.sent == []
    assert len(defaults) == 2
    await bot.close()


async def test_without_fallback_unknown_commands_stay_silent(project, monkeypatch):
    bot = await make_bot(project)
    defaults = []

    async def default_handler(self, ctx, error):
        defaults.append(error)

    monkeypatch.setattr(commands.Bot, 'on_command_error', default_handler)
    ctx = failed_command()
    await bot.on_command_error(ctx, commands.CommandNotFound('Command "nope" is not found'))
    assert ctx.sent == [] and len(defaults) == 1
    await bot.close()
