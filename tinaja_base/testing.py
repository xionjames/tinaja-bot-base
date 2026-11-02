"""Fakes for unit-testing cogs without connecting to Discord"""

from types import SimpleNamespace


def fake_member(name='member', bot=False, id=1):
    return SimpleNamespace(id=id, name=name, display_name=name, mention=f'@{name}', bot=bot)


def fake_message(content, author=None, mentions=(), id=None, channel=None):
    message = SimpleNamespace(
        id=id,
        content=content,
        author=author or fake_member(),
        mentions=list(mentions),
        channel=channel,
        replies=[],
        reactions=[],
    )

    async def reply(text):
        message.replies.append(text)

    async def add_reaction(emoji):
        message.reactions.append(emoji)

    message.reply = reply
    message.add_reaction = add_reaction
    return message


class FakeChannel:
    def __init__(self, messages=(), id=10):
        self.id = id
        self.messages = list(messages)  # oldest first, like a Discord channel reads top to bottom
        self.sent = []  # what was sent straight to the channel, e.g. by a Plugin

    async def send(self, message):
        self.sent.append(message)

    async def fetch_message(self, id):
        return next(m for m in self.messages if str(m.id) == str(id))

    async def history(self, limit=100):
        # Discord returns the newest messages first
        for message in list(reversed(self.messages))[:limit]:
            yield message


class FakeContext:
    def __init__(self, author=None, channel=None, message=None):
        self.author = author or fake_member()
        self.channel = channel or FakeChannel()
        # the message that invoked the Command
        self.message = message or fake_message('', self.author, channel=self.channel)
        self.sent = []

    async def send(self, message):
        self.sent.append(message)


async def run_command(cog, name, *args, ctx=None):
    """Run one of the cog's Commands like the bot would, returning what it sent"""
    ctx = ctx or FakeContext()
    command = next(c for c in cog.get_commands() if c.name == name)
    await cog.cog_load()
    try:
        await command.callback(cog, ctx, *args)
    finally:
        await cog.cog_unload()
    return ctx.sent
