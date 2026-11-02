# $bot_name
A Discord bot built on [tinaja-bot-base](https://github.com/xionjames/tinaja-bot-base), written in Go.

The bot runs on a small Python host that connects to Discord. Your code is a Go **plugin**: the host starts the
binary built from `plugin/` and passes it Commands, messages and mentions. The host speaks
[the plugin protocol](https://github.com/xionjames/tinaja-bot-base/blob/main/docs/protocol.md) with it over
stdin/stdout, and the `tinaja` package handles that for you.

## Project layout
- `bot.toml`: name, command prefix, intents, plain-text replies, @mention behaviour and the plugin
- `CONTEXT.md`: the glossary of the server's language, answered by `!glossary [term]`
- `plugin/`: the Go code of the bot (`main.go`), its `go.mod` and tests
- `.env`: the bot token (never commit it; copy `env.sample`). The plugin never sees it.

## Write commands
```go
plugin.Command("roll", "Rolls a die", func(ctx *tinaja.Context) error {
	ctx.Send(strconv.Itoa(rand.IntN(6) + 1))
	return nil
})

plugin.Command("recap", "The latest messages", func(ctx *tinaja.Context) error {  // ctx.Args: words after the Command
	messages, err := ctx.History(5)  // latest Member messages, oldest first
	if err != nil {
		return err
	}
	for _, m := range messages {
		ctx.Send(m.Author.DisplayName + ": " + m.Content)
	}
	return nil
})

plugin.OnMention(func(message *tinaja.Message, text string) error { message.Reply("You said: " + text); return nil })
```
The plugin is one long-running process, so package variables keep state between messages. A handler's error, or a
panic, is logged and the plugin keeps running. Log with the `log` package, which writes to stderr: stdout is reserved
for the protocol.

## Run manually
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Go, then install the dependencies
```bash
uv sync
(cd plugin && $go_get_step)
```
- Create a new `.env` file using `env.sample` as a template to set the required credentials.
- Build the plugin, after every change, then run the bot
```bash
(cd plugin && go build -o bot .)
uv run tinaja-bot run
```

## Run tests
```bash
cd plugin && go test ./...
```

## Docker
```bash
uv run tinaja-bot check                # is the bot ready to build? (build runs this first; needs plugin/bot built)
uv run tinaja-bot build                # docker build, tagged ghcr.io/<owner>/<repo>:latest and :<git sha>
docker run -it --env-file .env ghcr.io/<owner>/<repo>:latest
uv run tinaja-bot publish              # docker push; first: echo $CR_PAT | docker login ghcr.io -u <user> --password-stdin
```
The image builds the plugin itself as a static binary. Pushing to `main` on GitHub runs
`.github/workflows/build-and-push.yaml`. It tests and builds the plugin and runs `tinaja-bot check`, and only then
publishes a multi-arch image to `ghcr.io/<owner>/<repo>`.
