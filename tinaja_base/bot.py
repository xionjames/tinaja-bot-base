import discord
from discord.ext import commands

from tinaja_base.cogs.glossary import Glossary
from tinaja_base.cogs.mentions import Mentions
from tinaja_base.cogs.replies import format_reply, reply_commands
from tinaja_base.context import Context
from tinaja_base.loader import find_cogs


class BaseBot(commands.Bot):
    def __init__(self, config):
        intents = discord.Intents.default()
        intents.message_content = config.intents.message_content
        intents.members = config.intents.members
        intents.presences = config.intents.presences
        prefix = commands.when_mentioned_or(config.prefix) if config.mention_prefix else config.prefix
        super().__init__(command_prefix=prefix, intents=intents)

        self.config = config
        self.context = Context.from_file(config.context_path)

    async def setup_hook(self):
        # Runs once before connecting, unlike on_ready which fires on every reconnect
        await self.add_cog(Glossary(self.context))
        for command in reply_commands(self.config.replies, self.config.prefix):
            self.add_command(command)
        if self.config.mentions:
            await self.add_cog(Mentions(self, self.config.mention_reply))
        for cog in find_cogs(self.config.cogs_path):
            await self.add_cog(cog())

    async def on_command_error(self, ctx, error):
        # Only for the real prefix: '@Bot hi there' isn't a failed Command, the Mentions cog answers it
        if (
            isinstance(error, commands.CommandNotFound)
            and self.config.reply_fallback
            and ctx.prefix == self.config.prefix
        ):
            await ctx.send(format_reply(self.config.reply_fallback, ctx.author, self.config.prefix, ctx.invoked_with))
            return
        await super().on_command_error(ctx, error)

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
