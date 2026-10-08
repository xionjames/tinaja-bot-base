# Hello Bot
The example bot of [tinaja-bot-base](../..), generated with `tinaja-bot new "Hello Bot" --dir examples`.

- `!hello` → `World` ([cogs/hello.py](cogs/hello.py))
- `@Hello Bot hello` → `World`: mentions work as a command prefix (`[mentions] as_prefix` in [bot.toml](bot.toml))
- `@Hello Bot` with anything else → `World`, through the `on_mention` listener in [cogs/hello.py](cogs/hello.py)
- `!recap [n]` → the last *n* messages Members wrote in the channel ([cogs/recap.py](cogs/recap.py))
- `!ping` → `pong @you`, a plain-text reply defined in [bot.toml](bot.toml)
- `!anything-else` → `Sorry @you, I don't know !anything-else. Try !help`, the `fallback` reply in [bot.toml](bot.toml)
- `!glossary [term]` → definitions from [CONTEXT.md](CONTEXT.md)

Unlike a generated bot, it depends on the framework through the local path `../..`, so it always tests the code in
this repo. For the same reason the generated `Dockerfile` and GitHub workflow were removed: images need the git
source that generated bots use.

## Run
```bash
uv sync
cp env.sample .env   # then set DISCORD_BOT_TOKEN
uv run tinaja-bot run
```

## Run tests
```bash
uv run pytest
```
