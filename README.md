# Tinaja-bot-base
A small Python framework to build Discord bots for a custom server, based on
[tinaja-bot](https://github.com/StefanBS/tinaja-bot). A bot is just configuration plus the Python code of its commands:

```
my-bot/
  bot.toml      # name, prefix, intents, plain-text replies, @mention behaviour
  CONTEXT.md    # the server's glossary, answered by !glossary [term]
  cogs/         # your commands: every commands.Cog class here is loaded
  .env          # DISCORD_BOT_TOKEN (copy env.sample)
```

The framework is used straight from this git repository; it is not published to PyPI.

## Create a bot
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and clone this repo, then:
```bash
uv sync
uv run tinaja-bot new "My Bot" --dir ~/code    # creates ~/code/my-bot
cd ~/code/my-bot && uv sync && cp env.sample .env   # then set DISCORD_BOT_TOKEN in .env
uv run tinaja-bot run
```
The new bot depends on this repo through git (`[tool.uv.sources]` in its `pyproject.toml`), using this clone's
`origin` remote. Choose another source or version with `--source <git-url>` and `--rev <branch|tag|commit>`.
`--source <local path>` makes an editable dependency for working on the framework itself (it can't build images).

To add the framework to an existing project instead: `uv add git+https://github.com/xionjames/tinaja-bot-base`.

In the [Discord Developer Portal](https://discord.com/developers/applications), enable the **Message Content**
privileged intent for the bot (plus Server Members / Presence if you turn them on in `bot.toml`), and invite it with
the *Send Messages* and *Read Message History* permissions.

## Write commands
Commands are ordinary [discord.py](https://discordpy.readthedocs.io/) cogs with a no-argument constructor:
```python
# cogs/hello.py
from discord.ext import commands


class Hello(commands.Cog):
    @commands.command(name='hello')
    async def hello(self, ctx):
        await ctx.send('World')
```

Commands that only send text need no Python at all:
```toml
[replies]
ping = "pong {author}"   # {author} mentions whoever asked, {prefix} is the command prefix
```

### @mentions
```toml
[mentions]
as_prefix = true                          # "@Bot hello" works the same as "!hello"
reply = "Hi {author}! Try {prefix}help"   # optional: sent when the bot is mentioned without a Command
```
With a `[mentions]` table, a message that mentions the bot but isn't a Command fires an `on_mention` event:
```python
@commands.Cog.listener()
async def on_mention(self, message, text):  # text is the message without the mention
    await message.reply(f'You said: {text}')
```

### Reading the channel
With the `message_content` intent (on by default), cogs can read what Members write:
```python
from tinaja_base import recent_messages


@commands.command(name='recap')
async def recap(self, ctx):
    messages = await recent_messages(ctx.channel, limit=5)  # oldest first, bots left out
    await ctx.send('\n'.join(f'{m.author.display_name}: {m.content}' for m in messages))


@commands.Cog.listener()
async def on_message(self, message):  # every message the bot can see
    ...
```

### Glossary
`CONTEXT.md` documents the server's language, in the same format as tinaja-bot's. The bot also reads it:
`!glossary` lists the terms, `!glossary <term>` answers with a definition, and commands can use `ctx.bot.context` or
`Context.from_file('CONTEXT.md').lookup('member')`.

### Testing cogs
```python
from tinaja_base.testing import FakeChannel, FakeContext, fake_message, run_command


async def test_hello():
    assert await run_command(Hello(), 'hello') == ['World']
```
`FakeContext(channel=FakeChannel([fake_message('hi')]))` seeds a channel history for cogs that read it.

## Docker and ghcr.io
Every generated bot has a `Dockerfile` and a GitHub Actions workflow:
```bash
uv run tinaja-bot check                                                 # is the bot ready to build?
uv run tinaja-bot build [--platform linux/amd64,linux/arm64] [--push]   # tags ghcr.io/<owner>/<repo>:latest and :<sha>
uv run tinaja-bot publish                                               # docker push
docker run -it --env-file .env ghcr.io/<owner>/<repo>:latest
```
Log in before publishing: `echo $CR_PAT | docker login ghcr.io -u <github-user> --password-stdin`.
Pushing to `main` runs `.github/workflows/build-and-push.yaml`, which tests the bot and pushes a multi-arch image.

`tinaja-bot check` fails, and so stops both `build` and the workflow's image push, when the bot isn't ready:
- `tinaja-bot-base` comes from a local path, or its git URL / `rev` can't be reached (not pushed yet, or private)
- `Dockerfile` or `uv.lock` is missing, or `bot.toml` doesn't parse
- a cog fails to import, or the bot has nothing to do (no Cog commands or listeners, no `[replies]`)

An empty glossary is only a warning.
The image installs the framework from its git URL, so this repository must be reachable by Docker (public).

## Example
[`examples/hello-bot`](examples/hello-bot) answers `!hello` and any @mention with `World`, and `!recap [n]` with the
latest messages in the channel:
```bash
cd examples/hello-bot && uv sync && uv run pytest
```

## Develop the framework
```bash
uv sync
uv run pytest             # tests
uv run ruff check .       # lint (add --fix to apply safe fixes)
uv run ruff format .      # format
```
