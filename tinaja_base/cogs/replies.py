from discord.ext import commands


def format_reply(text, author, prefix):
    # Plain replace rather than str.format, so stray braces in bot.toml can't break a reply
    return text.replace('{author}', author.mention).replace('{prefix}', prefix)


def reply_commands(replies, prefix):
    """One Command per [replies] entry in bot.toml, each sending its text back"""
    return [_reply_command(name, text, prefix) for name, text in replies.items()]


def _reply_command(name, text, prefix):
    async def reply(ctx):
        await ctx.send(format_reply(text, ctx.author, prefix))

    return commands.Command(reply, name=name)
