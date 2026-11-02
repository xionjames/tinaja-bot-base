// $bot_name's Commands and listeners. The bot runs the built binary and talks to it over stdin/stdout,
// so log to stderr (the log package does): anything printed to stdout must be protocol messages.
package main

import (
	"log"

	tinaja "github.com/xionjames/tinaja-bot-base/sdk/go"
)

func newPlugin() *tinaja.Plugin {
	plugin := tinaja.New()

	plugin.Command("hello", "Says World", func(ctx *tinaja.Context) error {
		ctx.Send("World")
		return nil
	})

	plugin.OnMention(func(message *tinaja.Message, text string) error {
		message.Reply("World")
		return nil
	})

	return plugin
}

func main() {
	if err := newPlugin().Run(); err != nil {
		log.Fatal(err)
	}
}
