package main

import (
	"reflect"
	"testing"

	"github.com/xionjames/tinaja-bot-base/sdk/go/tinajatest"
)

func TestHelloAnswersWorld(t *testing.T) {
	sent, err := tinajatest.RunCommand(newPlugin(), tinajatest.Options{}, "hello")
	if err != nil || !reflect.DeepEqual(sent, []string{"World"}) {
		t.Fatalf("got %v, %v", sent, err)
	}
}

func TestMentionAnswersWorld(t *testing.T) {
	message := tinajatest.FakeMessage("<@42> hi")
	actions, _ := tinajatest.RunEvent(newPlugin(), map[string]any{"type": "mention", "message": message, "text": "hi"}, nil)
	want := []map[string]any{{"type": "send", "channel_id": "10", "content": "World", "reply_to": "100"}}
	if !reflect.DeepEqual(actions, want) {
		t.Fatalf("got %v", actions)
	}
}
