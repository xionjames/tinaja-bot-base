// The reference behaviour from sdk/conformance/README.md
package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/xionjames/tinaja-bot-base/sdk/go"
)

func main() {
	plugin := tinaja.New()

	plugin.Command("hello", "Says World", func(ctx *tinaja.Context) error {
		ctx.Send("World")
		return nil
	})

	plugin.Command("echo", "Repeats what you say", func(ctx *tinaja.Context) error {
		if len(ctx.Args) == 0 {
			ctx.Send("Nothing to echo")
		} else {
			ctx.Send(strings.Join(ctx.Args, " "))
		}
		return nil
	})

	plugin.Command("recap", "The latest messages in the channel", func(ctx *tinaja.Context) error {
		count := 5
		if len(ctx.Args) > 0 {
			count, _ = strconv.Atoi(ctx.Args[0])
		}
		messages, err := ctx.History(count)
		if err != nil {
			return err
		}
		lines := []string{}
		for _, m := range messages {
			lines = append(lines, m.Author.DisplayName+": "+m.Content)
		}
		if len(lines) == 0 {
			ctx.Send("Nothing to recap yet.")
		} else {
			ctx.Send(strings.Join(lines, "\n"))
		}
		return nil
	})

	plugin.OnMention(func(message *tinaja.Message, text string) error {
		message.Reply("You said: " + text)
		return nil
	})

	plugin.OnMessage(func(message *tinaja.Message) error {
		if message.Content == "ping" {
			message.React("🏓")
		}
		return nil
	})

	if err := plugin.Run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
