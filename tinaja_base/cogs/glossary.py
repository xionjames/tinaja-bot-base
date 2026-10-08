from discord.ext import commands


class Glossary(commands.Cog):
    """Answers questions about the Server's domain language, read from CONTEXT.md"""

    def __init__(self, context):
        self._context = context

    @commands.command(name='glossary')
    async def glossary(self, ctx, *words):
        if not words:
            if not self._context.terms:
                await ctx.send('The glossary is empty.')
                return
            names = ', '.join(sorted(term.name for term in self._context.terms.values()))
            await ctx.send(f'Glossary terms: {names}')
            return

        name = ' '.join(words)
        term = self._context.lookup(name)
        if term is None:
            await ctx.send(f'{ctx.author.mention} "{name}" is not in the glossary')
            return

        response = f'**{term.name}**: {term.definition}'
        if term.avoid:
            response += f'\n_Avoid_: {term.avoid}'
        await ctx.send(response)
