// Package tinajatest runs a Plugin's handlers without a Bot: what they send is recorded, history comes from a list.
package tinajatest

import (
	"encoding/json"
	"strings"

	"github.com/xionjames/tinaja-bot-base/sdk/go"
)

func FakeAuthor(name string) tinaja.AuthorData {
	return tinaja.AuthorData{ID: "1", Name: name, DisplayName: name, Mention: "<@1>"}
}

// FakeMessage is message 100 in channel 10, written by "member".
func FakeMessage(content string) tinaja.MessageData {
	return tinaja.MessageData{ID: "100", Content: content, ChannelID: "10", Author: FakeAuthor("member")}
}

// FakeConn records every action as a protocol message and answers History from Messages (oldest first).
type FakeConn struct {
	Actions  []map[string]any
	Messages []tinaja.MessageData
}

func (f *FakeConn) Write(action any) {
	raw, _ := json.Marshal(action)
	var message map[string]any
	_ = json.Unmarshal(raw, &message)
	f.Actions = append(f.Actions, message)
}

func (f *FakeConn) History(channelID string, limit int) ([]*tinaja.Message, error) {
	data := f.Messages
	if len(data) > limit {
		data = data[len(data)-limit:]
	}
	messages := make([]*tinaja.Message, 0, len(data))
	for _, d := range data {
		messages = append(messages, tinaja.NewMessage(d, f))
	}
	return messages, nil
}

// RunEvent dispatches one protocol event (anything that marshals to its JSON) and returns the actions it caused.
func RunEvent(p *tinaja.Plugin, event any, history []tinaja.MessageData) ([]map[string]any, error) {
	raw, err := json.Marshal(event)
	if err != nil {
		return nil, err
	}
	conn := &FakeConn{Messages: history}
	err = p.Dispatch(conn, raw)
	return conn.Actions, err
}

// Options change who runs a Command and what the channel history holds; the zero value is fine.
type Options struct {
	Author  *tinaja.AuthorData
	History []tinaja.MessageData
}

// RunCommand runs a Command like the Bot would, returning the text it sent (sends and replies).
func RunCommand(p *tinaja.Plugin, options Options, name string, args ...string) ([]string, error) {
	author := FakeAuthor("member")
	if options.Author != nil {
		author = *options.Author
	}
	if args == nil {
		args = []string{}
	}
	message := FakeMessage(strings.Join(append([]string{"!" + name}, args...), " "))
	message.Author = author
	event := map[string]any{"type": "command", "name": name, "args": args, "channel_id": "10", "author": author, "message": message}
	actions, err := RunEvent(p, event, options.History)
	sent := []string{}
	for _, action := range actions {
		if action["type"] == "send" {
			sent = append(sent, action["content"].(string))
		}
	}
	return sent, err
}
