# $bot_name
A Discord bot built on [tinaja-bot-base](https://github.com/xionjames/tinaja-bot-base), written in Ruby.

The bot runs on a small Python host that connects to Discord. Your code is a Ruby **plugin**: the host starts
`plugin/bot.rb` and passes it Commands, messages and mentions. The host speaks
[the plugin protocol](https://github.com/xionjames/tinaja-bot-base/blob/main/docs/protocol.md) with it over
stdin/stdout, and the `tinaja` gem handles that for you.

## Project layout
- `bot.toml`: name, command prefix, intents, plain-text replies, @mention behaviour and the plugin
- `CONTEXT.md`: the glossary of the server's language, answered by `!glossary [term]`
- `plugin/`: the Ruby code of the bot (`bot.rb`), its `Gemfile` and tests
- `.env`: the bot token (never commit it; copy `env.sample`). The plugin never sees it.

## Write commands
```ruby
PLUGIN.command('roll', help: 'Rolls a die') { |ctx| ctx.send(rand(1..6).to_s) }  # !roll

PLUGIN.command('recap') do |ctx|                      # ctx.args are the words after the Command
  messages = ctx.history((ctx.args.first || 5).to_i)  # latest Member messages, oldest first
  ctx.send(messages.map { |m| "#{m.author.display_name}: #{m.content}" }.join("\n"))
end

PLUGIN.on_message { |message| message.react('👋') if message.content.include?('hola') }
PLUGIN.on_mention { |message, text| message.reply("You said: #{text}") }
```
The plugin is one long-running process, so plain Ruby variables keep state between messages. Use any gem: add it to
`plugin/Gemfile` and run `bundle install`. Print logs with `warn`: stdout is reserved for the protocol.

## Run manually
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Ruby, then install the dependencies
```bash
uv sync
(cd plugin && bundle install)
```
- Create a new `.env` file using `env.sample` as a template to set the required credentials.
- Run the bot
```bash
uv run tinaja-bot run
```

## Run tests
```bash
cd plugin && bundle exec rake test
```

## Docker
The image builds on Linux, so add Linux to the gem lockfile once:
```bash
(cd plugin && bundle lock --add-platform x86_64-linux aarch64-linux)
```
```bash
uv run tinaja-bot check                # is the bot ready to build? (build runs this first)
uv run tinaja-bot build                # docker build, tagged ghcr.io/<owner>/<repo>:latest and :<git sha>
docker run -it --env-file .env ghcr.io/<owner>/<repo>:latest
uv run tinaja-bot publish              # docker push; first: echo $CR_PAT | docker login ghcr.io -u <user> --password-stdin
```
Pushing to `main` on GitHub runs `.github/workflows/build-and-push.yaml`. It tests the plugin and runs
`tinaja-bot check`, and only then publishes a multi-arch image to `ghcr.io/<owner>/<repo>`.
