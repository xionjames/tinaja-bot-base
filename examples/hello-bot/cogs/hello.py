from discord.ext import commands


class Hello(commands.Cog):
    @commands.command(name='hello')
    async def hello(self, ctx):
        await ctx.send('World')

    @commands.Cog.listener()
    async def on_mention(self, message, text):
        # Fired when a Member @mentions the bot with anything that isn't a Command
        await message.reply('World')
