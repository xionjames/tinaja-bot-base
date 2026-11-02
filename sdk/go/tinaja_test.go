package tinaja_test

import (
	"bytes"
	"encoding/json"
	"errors"
	"reflect"
	"strings"
	"testing"

	"github.com/xionjames/tinaja-bot-base/sdk/go"
	"github.com/xionjames/tinaja-bot-base/sdk/go/tinajatest"
)

func makePlugin() *tinaja.Plugin {
	plugin := tinaja.New()
	plugin.Command("hello", "Says World", func(ctx *tinaja.Context) error {
		ctx.Send("World, " + ctx.Author.DisplayName)
		return nil
	})
	plugin.Command("last", "", func(ctx *tinaja.Context) error {
		messages, err := ctx.History(1)
		if err != nil {
			return err
		}
		ctx.Reply(messages[0].Content)
		return nil
	})
	plugin.OnMessage(func(message *tinaja.Message) error {
		message.React("🏓")
		return nil
	})
	return plugin
}

func check(t *testing.T, got, want any) {
	t.Helper()
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %#v, want %#v", got, want)
	}
}

func TestRunCommandReturnsWhatWasSent(t *testing.T) {
	jane := tinajatest.FakeAuthor("jane")
	sent, err := tinajatest.RunCommand(makePlugin(), tinajatest.Options{Author: &jane}, "hello")
	check(t, err, nil)
	check(t, sent, []string{"World, jane"})
}

func TestHistoryComesFromTheGivenMessages(t *testing.T) {
	history := []tinaja.MessageData{tinajatest.FakeMessage("old"), tinajatest.FakeMessage("new")}
	sent, _ := tinajatest.RunCommand(makePlugin(), tinajatest.Options{History: history}, "last")
	check(t, sent, []string{"new"})
}

func TestRunEventReturnsActions(t *testing.T) {
	message := tinajatest.FakeMessage("ping")
	message.ID = "7"
	actions, _ := tinajatest.RunEvent(makePlugin(), map[string]any{"type": "message", "message": message}, nil)
	check(t, actions, []map[string]any{{"type": "react", "channel_id": "10", "message_id": "7", "emoji": "🏓"}})
}

func TestRegistrationListsCommandsAndEvents(t *testing.T) {
	check(t, makePlugin().Registration(), tinaja.Registration{
		Type:     "register",
		Commands: []tinaja.CommandInfo{{Name: "hello", Help: "Says World"}, {Name: "last", Help: ""}},
		Events:   []string{"message"},
	})
}

func TestAFailingHandlerDoesNotStopThePlugin(t *testing.T) {
	plugin := makePlugin()
	plugin.Command("boom", "", func(ctx *tinaja.Context) error { return errors.New("boom") })
	plugin.Command("panic", "", func(ctx *tinaja.Context) error { panic("oh no") })
	input := strings.Join([]string{
		`{"type": "hello", "protocol": 1, "bot": {}}`,
		`{"type": "command", "name": "boom", "args": [], "channel_id": "10"}`,
		`{"type": "command", "name": "panic", "args": [], "channel_id": "10"}`,
		`{"type": "command", "name": "hello", "args": [], "channel_id": "10", "author": {"name": "jane"}}`,
	}, "\n")
	var output bytes.Buffer
	check(t, plugin.RunWith(strings.NewReader(input), &output), nil)
	var types []string
	var last map[string]any
	for _, line := range strings.Split(strings.TrimSpace(output.String()), "\n") {
		_ = json.Unmarshal([]byte(line), &last)
		types = append(types, last["type"].(string))
	}
	check(t, types, []string{"register", "send"})
	check(t, last["content"], "World, jane")
}
