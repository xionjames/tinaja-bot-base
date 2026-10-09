# AGENTS.md

Guidance for AI coding agents (Claude, Codex, Copilot, Cursor, Gemini, ...) working in this repository.
Human-facing docs live in [README.md](README.md); read it for the user-facing behaviour of the framework.

## What this is
`tinaja-bot-base` is a small Python framework for building prefix-command Discord bots on top of discord.py.
A Bot is a folder with `bot.toml`, `CONTEXT.md` (glossary), a `cogs/` directory and a `.env` token.
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
Before calling a change done, run lint, format check and tests for the framework and, if the change can affect bots,
for `examples/hello-bot`. That's exactly what [.github/workflows/test.yaml](.github/workflows/test.yaml) runs.

## Layout
```
tinaja_base/
  bot.py         BaseBot: builds intents/prefix from Config, loads built-in cogs, replies and user cogs
  config.py      parses bot.toml into Config / Intents
  context.py     parses CONTEXT.md into a glossary (Context, Term)
  loader.py      find_cogs(): imports cogs/*.py and returns every commands.Cog defined there
  channel.py     recent_messages() helper
  cli.py         `tinaja-bot` CLI: new, run, check, build, publish
  testing.py     fakes (FakeContext, FakeChannel, fake_message, run_command) for testing cogs offline
  cogs/          built-in cogs: glossary, mentions, replies
  templates/new_bot/   files copied by `tinaja-bot new`
tests/           pytest suite for the framework
examples/hello-bot/    a complete Bot using the framework
```
Public API is what [tinaja_base/__init__.py](tinaja_base/__init__.py) exports plus `tinaja_base.testing`.
Changing either is a breaking change for existing bots; call it out.

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
- Never commit `.env` or tokens; `env.sample` is the only token file in git.

## Working style
- Ask before assuming when a request is ambiguous; surface the ambiguity explicitly.
- Only touch files related to the task. If something adjacent looks wrong, mention it instead of fixing it silently.
- Say when you're unsure rather than guessing about discord.py behaviour or Discord API details.
- Don't commit or push unless asked.
