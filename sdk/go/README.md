# tinaja (Go SDK)
Write the Commands and listeners of a [tinaja-bot-base](../..) Bot in Go, using only the standard library.
`tinaja-bot new "My Bot" --lang go` sets everything up. To add it by hand:
```bash
go get github.com/xionjames/tinaja-bot-base/sdk/go@main
```
```go
import tinaja "github.com/xionjames/tinaja-bot-base/sdk/go"

plugin := tinaja.New()
plugin.Command("hello", "Says World", func(ctx *tinaja.Context) error {  // ctx.Args, ctx.Author, ctx.Reply
	ctx.Send("World")
	return nil
})
plugin.OnMessage(func(message *tinaja.Message) error { return nil })
plugin.OnMention(func(message *tinaja.Message, text string) error { message.Reply("You said: " + text); return nil })
log.Fatal(plugin.Run())
```
- `Context`: `Name`, `Args`, `ChannelID`, `Author`, `Message`, `Send(text)`, `Reply(text)`, `History(limit)`
- `Message`: `ID`, `Content`, `ChannelID`, `Author`, `Reply(text)`, `React(emoji)`
- `Author`: `ID`, `Name`, `DisplayName`, `Mention`, `Bot`
- `plugin.Send(channelID, text)` and `plugin.History(channelID, limit)`, from the handlers' goroutine

Handlers run one at a time. A returned error or a panic is logged to stderr and the Plugin keeps running.

## Testing
```go
import "github.com/xionjames/tinaja-bot-base/sdk/go/tinajatest"

sent, err := tinajatest.RunCommand(plugin, tinajatest.Options{}, "hello")             // []string{"World"}
history := []tinaja.MessageData{tinajatest.FakeMessage("hi")}
sent, err = tinajatest.RunCommand(plugin, tinajatest.Options{History: history}, "recap", "5")
actions, err := tinajatest.RunEvent(plugin, map[string]any{"type": "message", "message": tinajatest.FakeMessage("bot?")}, nil)
```

## Develop
```bash
go vet ./... && go test ./...
go build -o conformance-plugin ./conformance && uv run python ../conformance/run.py -- ./conformance-plugin
```
