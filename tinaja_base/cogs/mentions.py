import re

from discord.ext import commands

from tinaja_base.cogs.replies import format_reply


class Mentions(commands.Cog):
    """Turns a message that @mentions the bot, but isn't a Command, into an on_mention(message, text) event"""

    def __init__(self, bot, reply=None):
        self._bot = bot
        self._reply = reply

    @commands.Cog.listener()
    async def on_message(self, message):
        me = self._bot.user
        if message.author.bot or not any(user.id == me.id for user in message.mentions):
            return
        # Commands, including '@Bot hello' when mentions work as a prefix, are already handled by the bot
        ctx = await self._bot.get_context(message)
        if ctx.valid:
            return

        text = ' '.join(re.sub(rf'<@!?{me.id}>', '', message.content).split())
        self._bot.dispatch('mention', message, text)
        if self._reply:
            await message.reply(format_reply(self._reply, message.author, self._bot.config.prefix))
