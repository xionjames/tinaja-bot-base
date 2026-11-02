# AGENTS.md

Guidance for AI coding agents (Claude, Codex, Copilot, Cursor, Gemini, ...) working in this repository.
Human-facing docs live in [README.md](README.md); read it for the user-facing behaviour of the framework.

## What this is
`tinaja-bot-base` is a small Python framework for building prefix-command Discord bots on top of discord.py.
A Bot is a folder with `bot.toml`, `CONTEXT.md` (glossary), a `cogs/` directory and a `.env` token. A Bot's code can
also be a Plugin in another language: a process the Bot talks to over stdin/stdout ([docs/protocol.md](docs/protocol.md)).
The framework is consumed from git, not PyPI.

## Commands
Use `uv` for everything; don't call `pip` or a bare `python`.
```bash
uv sync                         # install (CI uses: uv sync --locked)
uv run pytest                   # tests
uv run ruff check .             # lint
uv run ruff format .            # format
```
The example bot is a separate uv project and is checked in CI too:
```bash
cd examples/hello-bot && uv sync && uv run ruff check . && uv run ruff format --check . && uv run pytest
```
SDKs are tested with their own tools plus the language-agnostic conformance runner:
```bash
cd sdk/ruby && bundle exec rake test                                    # Ruby SDK
uv run python sdk/conformance/run.py -- ruby sdk/ruby/conformance/plugin.rb
cd examples/ruby-bot/plugin && bundle exec rake test                    # Ruby example
npm test                                                                # TypeScript SDK (no dependencies)
uv run python sdk/conformance/run.py -- node sdk/ts/conformance/plugin.ts
cd sdk/go && gofmt -l . && go vet ./... && go test ./... && go build -o conformance-plugin ./conformance  # Go SDK
uv run python sdk/conformance/run.py -- sdk/go/conformance-plugin
```
The Java SDK has no build tool on purpose: CI and [jitpack.yml](jitpack.yml) build it with `javac`; see the `java` job
in [.github/workflows/test.yaml](.github/workflows/test.yaml) for the commands. That job also builds generated Java and
Kotlin Bots with Gradle.
The Python SDK's tests (`sdk/python/tests`, including conformance) run with the framework's `uv run pytest`.
Before calling a change done, run lint, format check and tests for the framework and, if the change can affect bots,
for `examples/hello-bot`. That's exactly what [.github/workflows/test.yaml](.github/workflows/test.yaml) runs.

## Creating a Bot
```bash
uv run tinaja-bot new "My Bot" --dir ~/code      # creates ~/code/my-bot
cd ~/code/my-bot && uv sync && cp env.sample .env  # then set DISCORD_BOT_TOKEN in .env
uv run tinaja-bot run
```
Pass `--source <local path>` to `new` to depend on this clone (editable) while changing the framework and a Bot
together. Behaviour goes in the Bot's `bot.toml` (Replies), `CONTEXT.md` (glossary) and `cogs/` (Python Cogs).
The generated folder's README covers running, testing, `check` / `build` / `publish` and Docker; see also
[examples/hello-bot](examples/hello-bot) and the root [README.md](README.md).

## Layout
```
tinaja_base/
  bot.py         BaseBot: builds intents/prefix from Config, loads built-in cogs, replies and user cogs
  config.py      parses bot.toml into Config / Intents
  context.py     parses CONTEXT.md into a glossary (Context, Term)
  loader.py      find_cogs(): imports cogs/*.py and returns every commands.Cog defined there
  channel.py     recent_messages() helper
  cli.py         `tinaja-bot` CLI: new, run, check, build, publish
  plugins.py     PluginCog / PluginProcess: runs [plugins.*] processes and speaks docs/protocol.md with them
  testing.py     fakes (FakeContext, FakeChannel, fake_message, run_command) for testing cogs offline
  cogs/          built-in cogs: glossary, mentions, replies
  templates/new_bot/   files copied by `tinaja-bot new`
  templates/languages/<lang>/   per-language files that add to or replace new_bot (see LANGUAGES in cli.py)
tests/           pytest suite for the framework
docs/protocol.md       the Plugin protocol: the contract every SDK implements
sdk/<lang>/            one SDK per language, each with a conformance/ Plugin
sdk/conformance/       recorded exchanges (fixtures/*.jsonl) and run.py, which replays them against any Plugin
examples/hello-bot/    a complete Bot using the framework
examples/ruby-bot/     the same Bot as a Ruby Plugin
```
Public API is what [tinaja_base/__init__.py](tinaja_base/__init__.py) exports plus `tinaja_base.testing`, the Plugin
protocol and each SDK's API. Changing any of them in an incompatible way is a breaking change for existing bots; call it
out.

## Conventions
- Python >= 3.14, line length 120, **single quotes** (ruff format enforces it), ruff rules `I`, `UP`, `B`.
- Keep code small and direct: no abstraction layers for single-use code. Match the existing comment style: short
  comments that explain *why*, docstrings only where a function's contract isn't obvious.
- Tests are async-friendly (`asyncio_mode = "auto"`): write `async def test_...` with no decorator. Never connect to
  Discord in tests; use the fakes in `tinaja_base/testing.py`.
- Use the domain vocabulary from [CONTEXT.md](CONTEXT.md) in code, comments and docs: Bot, Server, Member, Command,
  Reply, Cog, Mention, Glossary term. Avoid the listed alternatives (e.g. "user", "plugin", "slash command").
- Only prefix Commands are supported; don't add slash commands unless asked.

## Gotchas
- **Templates** in `tinaja_base/templates/new_bot/` are rendered with `string.Template.safe_substitute`, so `$name`
  placeholders are substituted while `${{ github.* }}` survives. Dotfiles are stored as `dot-<name>` (e.g.
  `dot-gitignore`) and renamed on copy. Templates are excluded from ruff.
- `examples/` is excluded from the root ruff config; each example has its own `pyproject.toml` and `uv.lock`.
- If you change user-visible behaviour (CLI flags, `bot.toml` keys, testing helpers), update README.md, the template
  and the example bot so they stay consistent.
- `fallback` under `[replies]` is reserved: it answers unknown Commands and is not itself a Command.
- Never commit `.env` or tokens; `env.sample` is the only token file in git. Plugins never get `DISCORD_BOT_TOKEN`.
- **Protocol changes** must stay backward compatible: add message types or optional fields, never rename or remove
  them. Ids are strings (snowflakes overflow JavaScript numbers). Change [docs/protocol.md](docs/protocol.md), the
  fixtures in `sdk/conformance/fixtures` and every SDK together; the conformance runner catches SDKs left behind.
- A Plugin's stdout is the protocol: SDKs and Plugins log to stderr.
- The root `package.json` is the TypeScript SDK's package: npm can't install a git dependency from a subfolder, so
  Bots depend on `git+<repo>.git#<rev>` and `exports` points into `sdk/ts`. The SDK is plain ESM JavaScript with
  handwritten `.d.ts` files, so it needs no build step; keep the two in sync.
- `jitpack.yml` publishes the Java SDK as `com.github.<owner>:tinaja-bot-base:<branch>-SNAPSHOT` (or a tag or commit).
  Java and Kotlin templates share the `jvm` overlay (`OVERLAYS` in cli.py). A Plugin's stdout is the protocol, so
  JVM Plugins run Gradle's `installDist` start script, never `gradle run`.

## Working style
- Ask before assuming when a request is ambiguous; surface the ambiguity explicitly.
- Only touch files related to the task. If something adjacent looks wrong, mention it instead of fixing it silently.
- Say when you're unsure rather than guessing about discord.py behaviour or Discord API details.
- Don't commit or push unless asked.
