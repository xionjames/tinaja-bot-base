# $bot_name
A Discord bot built on [tinaja-bot-base](https://github.com/xionjames/tinaja-bot-base), written in Python.

## Project layout
- `bot.toml`: name, command prefix, intents, plain-text replies and @mention behaviour
- `CONTEXT.md`: the glossary of the server's language, answered by `!glossary [term]`
- `cogs/`: Python commands; every `commands.Cog` class in this folder is loaded
- `.env`: the bot token (never commit it; copy `env.sample`)

## Run manually
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then install the dependencies
```bash
uv sync
```
- Create a new `.env` file using `env.sample` as a template to set the required credentials.
- Run the bot
```bash
uv run tinaja-bot run
```

## Docker
```bash
uv run tinaja-bot check                # is the bot ready to build? (build runs this first)
uv run tinaja-bot build                # docker build, tagged ghcr.io/<owner>/<repo>:latest and :<git sha>
docker run -it --env-file .env ghcr.io/<owner>/<repo>:latest
uv run tinaja-bot publish              # docker push; first: echo $CR_PAT | docker login ghcr.io -u <user> --password-stdin
```
Pushing to `main` on GitHub runs `.github/workflows/build-and-push.yaml`, which tests the bot, runs
`tinaja-bot check` and only then publishes a multi-arch image to `ghcr.io/<owner>/<repo>`.

## Run tests
```bash
uv run pytest
```

## Lint and format
```bash
uv run ruff check .       # lint (add --fix to apply safe fixes)
uv run ruff format .      # format
```
