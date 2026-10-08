from discord.ext import commands
from tinaja_base import recent_messages


class Recap(commands.Cog):
    @commands.command(name='recap')
    async def recap(self, ctx, count: int = 5):
        # +1 because the !recap message itself is the newest one in the channel
        messages = await recent_messages(ctx.channel, limit=min(count, 20) + 1)
        lines = [f'{m.author.display_name}: {m.content}' for m in messages if m.id != ctx.message.id]
        await ctx.send('\n'.join(lines[-count:]) or 'Nothing to recap yet.')
