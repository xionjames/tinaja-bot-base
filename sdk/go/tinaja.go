// Package tinaja is the SDK for tinaja-bot-base Plugins: a Bot's Commands and listeners written in Go.
// The Bot (a Python host) runs this program and talks to it over stdin/stdout, see docs/protocol.md.
package tinaja

import (
	"bufio"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"runtime/debug"
	"sort"
	"strconv"
)

// Protocol is the protocol version this SDK speaks.
const Protocol = 1

// AuthorData and MessageData are the protocol's JSON shapes.
type AuthorData struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	DisplayName string `json:"display_name"`
	Mention     string `json:"mention"`
	Bot         bool   `json:"bot"`
}

type MessageData struct {
	ID        string     `json:"id"`
	Content   string     `json:"content"`
	ChannelID string     `json:"channel_id"`
	Author    AuthorData `json:"author"`
}

type Author struct {
	ID, Name, DisplayName, Mention string
	Bot                            bool
}

func newAuthor(data AuthorData) Author {
	displayName := data.DisplayName
	if displayName == "" {
		displayName = data.Name
	}
	return Author{ID: data.ID, Name: data.Name, DisplayName: displayName, Mention: data.Mention, Bot: data.Bot}
}

// Conn is where a Plugin's actions go: the host over stdio, or a fake in tests (see package tinajatest).
type Conn interface {
	Write(action any)
	History(channelID string, limit int) ([]*Message, error)
}

type sendAction struct {
	Type      string `json:"type"`
	ChannelID string `json:"channel_id"`
	Content   string `json:"content"`
	ReplyTo   string `json:"reply_to,omitempty"`
}

type reactAction struct {
	Type      string `json:"type"`
	ChannelID string `json:"channel_id"`
	MessageID string `json:"message_id"`
	Emoji     string `json:"emoji"`
}

type Message struct {
	ID, Content, ChannelID string
	Author                 Author
	conn                   Conn
}

func NewMessage(data MessageData, conn Conn) *Message {
	return &Message{ID: data.ID, Content: data.Content, ChannelID: data.ChannelID, Author: newAuthor(data.Author), conn: conn}
}

func (m *Message) Reply(content string) {
	m.conn.Write(sendAction{Type: "send", ChannelID: m.ChannelID, Content: content, ReplyTo: m.ID})
}

func (m *Message) React(emoji string) {
	m.conn.Write(reactAction{Type: "react", ChannelID: m.ChannelID, MessageID: m.ID, Emoji: emoji})
}

// Context is what a Command handler gets: who asked, where, and the words after the Command.
type Context struct {
	Name      string
	Args      []string
	ChannelID string
	Author    Author
	Message   *Message
	conn      Conn
}

func (c *Context) Send(content string) {
	c.conn.Write(sendAction{Type: "send", ChannelID: c.ChannelID, Content: content})
}

func (c *Context) Reply(content string) { c.Message.Reply(content) }

// History returns the channel's latest Member messages, oldest first.
func (c *Context) History(limit int) ([]*Message, error) { return c.conn.History(c.ChannelID, limit) }

type event struct {
	Type      string        `json:"type"`
	Name      string        `json:"name"`
	Args      []string      `json:"args"`
	ChannelID string        `json:"channel_id"`
	Author    AuthorData    `json:"author"`
	Message   MessageData   `json:"message"`
	Text      string        `json:"text"`
	Bot       BotInfo       `json:"bot"`
	RequestID string        `json:"request_id"`
	Messages  []MessageData `json:"messages"`
	Error     string        `json:"error"`
}

// BotInfo is the hello's description of the Bot; ID is empty while it isn't logged in.
type BotInfo struct {
	Name   string  `json:"name"`
	Prefix string  `json:"prefix"`
	ID     *string `json:"id"`
}

type command struct {
	name, help string
	handler    func(*Context) error
}

type Plugin struct {
	Bot             BotInfo
	commands        []command
	messageHandlers []func(*Message) error
	mentionHandlers []func(*Message, string) error
	conn            Conn
}

func New() *Plugin { return &Plugin{} }

// Command registers handler for every !name; help is shown by !help.
func (p *Plugin) Command(name, help string, handler func(*Context) error) {
	p.commands = append(p.commands, command{name, help, handler})
}

// OnMessage registers handler for every message from a Member, Commands included.
func (p *Plugin) OnMessage(handler func(*Message) error) {
	p.messageHandlers = append(p.messageHandlers, handler)
}

// OnMention registers handler for when the Bot is @mentioned without a Command; needs [mentions] in bot.toml.
func (p *Plugin) OnMention(handler func(message *Message, text string) error) {
	p.mentionHandlers = append(p.mentionHandlers, handler)
}

// Send and History work outside Command handlers too. The connection isn't safe for concurrent use, so call them
// from the goroutine that runs the handlers.
func (p *Plugin) Send(channelID, content string) {
	p.conn.Write(sendAction{Type: "send", ChannelID: channelID, Content: content})
}

func (p *Plugin) History(channelID string, limit int) ([]*Message, error) {
	return p.conn.History(channelID, limit)
}

type CommandInfo struct {
	Name string `json:"name"`
	Help string `json:"help"`
}

type Registration struct {
	Type     string        `json:"type"`
	Commands []CommandInfo `json:"commands"`
	Events   []string      `json:"events"`
}

func (p *Plugin) Registration() Registration {
	registration := Registration{Type: "register", Commands: []CommandInfo{}, Events: []string{}}
	for _, c := range p.commands {
		registration.Commands = append(registration.Commands, CommandInfo{c.name, c.help})
	}
	if len(p.messageHandlers) > 0 {
		registration.Events = append(registration.Events, "message")
	}
	if len(p.mentionHandlers) > 0 {
		registration.Events = append(registration.Events, "mention")
	}
	sort.Strings(registration.Events)
	return registration
}

// Run serves the host over stdin/stdout until it says shutdown or closes stdin.
func (p *Plugin) Run() error { return p.RunWith(os.Stdin, os.Stdout) }

func (p *Plugin) RunWith(r io.Reader, w io.Writer) error {
	conn := newStdioConn(r, w)
	for {
		raw, err := conn.read()
		if err != nil || raw == nil {
			return err
		}
		var kind struct {
			Type string `json:"type"`
		}
		if json.Unmarshal(raw, &kind) == nil && kind.Type == "shutdown" {
			return conn.err
		}
		p.handle(conn, raw)
		if conn.err != nil {
			return conn.err
		}
	}
}

// handle dispatches one event, logging handler errors and panics: one failing handler mustn't stop the Plugin.
func (p *Plugin) handle(conn Conn, raw []byte) {
	defer func() {
		if r := recover(); r != nil {
			fmt.Fprintf(os.Stderr, "tinaja: handler panicked: %v\n%s", r, debug.Stack())
		}
	}()
	if err := p.Dispatch(conn, raw); err != nil {
		fmt.Fprintf(os.Stderr, "tinaja: %v\n", err)
	}
}

// Dispatch handles one protocol event (a JSON object), returning the handler's error.
func (p *Plugin) Dispatch(conn Conn, raw []byte) error {
	p.conn = conn
	var e event
	if err := json.Unmarshal(raw, &e); err != nil {
		return fmt.Errorf("bad event %q: %w", raw, err)
	}
	switch e.Type {
	case "hello":
		p.Bot = e.Bot
		conn.Write(p.Registration())
	case "command":
		for _, c := range p.commands {
			if c.name == e.Name {
				args := e.Args
				if args == nil {
					args = []string{}
				}
				ctx := &Context{Name: e.Name, Args: args, ChannelID: e.ChannelID, Author: newAuthor(e.Author),
					Message: NewMessage(e.Message, conn), conn: conn}
				return c.handler(ctx)
			}
		}
	case "message":
		for _, handler := range p.messageHandlers {
			if err := handler(NewMessage(e.Message, conn)); err != nil {
				return err
			}
		}
	case "mention":
		for _, handler := range p.mentionHandlers {
			if err := handler(NewMessage(e.Message, conn), e.Text); err != nil {
				return err
			}
		}
	case "error":
		fmt.Fprintf(os.Stderr, "tinaja: the host reported an error: %s\n", e.Error)
	}
	// anything else (ready, future events) needs no answer
	return nil
}

// stdioConn is JSON lines over a reader and a writer.
type stdioConn struct {
	scanner *bufio.Scanner
	encoder *json.Encoder
	pending [][]byte // events that arrived while waiting for a result
	nextID  int
	err     error // the first write error; Run returns it
}

func newStdioConn(r io.Reader, w io.Writer) *stdioConn {
	scanner := bufio.NewScanner(r)
	scanner.Buffer(make([]byte, 64*1024), 16*1024*1024)
	encoder := json.NewEncoder(w)
	encoder.SetEscapeHTML(false)
	return &stdioConn{scanner: scanner, encoder: encoder, nextID: 1}
}

func (c *stdioConn) Write(action any) {
	if err := c.encoder.Encode(action); err != nil && c.err == nil {
		c.err = err
	}
}

// read returns the next event, or nil when the host closed stdin.
func (c *stdioConn) read() ([]byte, error) {
	if len(c.pending) > 0 {
		raw := c.pending[0]
		c.pending = c.pending[1:]
		return raw, nil
	}
	return c.readLine()
}

func (c *stdioConn) readLine() ([]byte, error) {
	for c.scanner.Scan() {
		if line := c.scanner.Bytes(); len(line) > 0 {
			return append([]byte(nil), line...), nil
		}
	}
	return nil, c.scanner.Err()
}

func (c *stdioConn) History(channelID string, limit int) ([]*Message, error) {
	requestID := strconv.Itoa(c.nextID)
	c.nextID++
	c.Write(struct {
		Type      string `json:"type"`
		RequestID string `json:"request_id"`
		ChannelID string `json:"channel_id"`
		Limit     int    `json:"limit"`
	}{"history", requestID, channelID, limit})
	for {
		raw, err := c.readLine()
		if err != nil {
			return nil, err
		}
		if raw == nil {
			return nil, errors.New("the host closed the connection")
		}
		var e event
		if json.Unmarshal(raw, &e) == nil && e.RequestID == requestID && (e.Type == "result" || e.Type == "error") {
			if e.Type == "error" {
				return nil, errors.New(e.Error)
			}
			messages := make([]*Message, 0, len(e.Messages))
			for _, data := range e.Messages {
				messages = append(messages, NewMessage(data, c))
			}
			return messages, nil
		}
		c.pending = append(c.pending, raw)
	}
}
