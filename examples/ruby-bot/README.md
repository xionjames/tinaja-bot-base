# Ruby Bot
The Ruby example of [tinaja-bot-base](../..): the same Bot as [hello-bot](../hello-bot), with its Commands written in
Ruby as a [plugin](../../docs/protocol.md). It was generated with `tinaja-bot new "Ruby Bot" --dir examples --lang ruby`.

- `!hello` → `World` ([plugin/bot.rb](plugin/bot.rb))
- `@Ruby Bot` with anything that isn't a Command → `World`, through `on_mention`
- `!recap [n]` → the last *n* messages Members wrote in the channel
- `!seen` → how many messages each Member wrote since the bot started, counted by `on_message`
- `!ping`, the fallback reply and `!glossary` come from [bot.toml](bot.toml) and [CONTEXT.md](CONTEXT.md), as in
  every Bot

Like hello-bot, it depends on the framework and the `tinaja` gem through local paths, so it always tests the code in
this repo. The generated `Dockerfile` and GitHub workflow were removed for that reason.

## Run
```bash
uv sync
(cd plugin && bundle install)
cp env.sample .env   # then set DISCORD_BOT_TOKEN
uv run tinaja-bot run
```

## Run tests
```bash
cd plugin && bundle exec rake test
```
