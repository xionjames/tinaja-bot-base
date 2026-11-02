"""The reference behaviour from sdk/conformance/README.md"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tinaja_plugin import Plugin

plugin = Plugin()


@plugin.command('hello', help='Says World')
def hello(ctx):
    ctx.send('World')


@plugin.command('echo', help='Repeats what you say')
def echo(ctx):
    ctx.send(' '.join(ctx.args) or 'Nothing to echo')


@plugin.command('recap', help='The latest messages in the channel')
def recap(ctx):
    count = int(ctx.args[0]) if ctx.args else 5
    messages = ctx.history(count)
    ctx.send('\n'.join(f'{m.author.display_name}: {m.content}' for m in messages) or 'Nothing to recap yet.')


@plugin.on_mention
def mention(message, text):
    message.reply(f'You said: {text}')


@plugin.on_message
def ping(message):
    if message.content == 'ping':
        message.react('🏓')


if __name__ == '__main__':
    plugin.run()
