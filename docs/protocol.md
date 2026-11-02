# Plugin protocol, version 1
A **Plugin** is a long-running process, written in any language, that adds Commands and listeners to a Bot. The Bot
(the Python host) keeps the Discord connection and talks to each Plugin over the Plugin's stdin and stdout.

The SDKs in [`sdk/`](../sdk) implement this protocol; read this page to write a Plugin without one, or a new SDK.

## Running a Plugin
```toml
# bot.toml
[plugins.main]
cwd = "plugin"                    # relative to the Bot folder; default: the Bot folder
run = "bundle exec ruby bot.rb"   # split like a shell would, but run without a shell
```
- The host starts `run` in `cwd` when the Bot starts and stops it when the Bot stops.
- The Plugin gets the host's environment **without `DISCORD_BOT_TOKEN`**: it never sees the token.
- stderr is not part of the protocol: it goes straight to the Bot's log, so print debugging output there.
- If the Plugin exits, the host logs it and starts it again, waiting a bit longer after each crash (up to 30s).

## Messages
Every message is one JSON object on one line (UTF-8, `\n` terminated), with a `type`. Both sides ignore fields they
don't know, so new fields can be added without breaking anything.

**Discord ids are strings** (`"1234567890123456789"`): they don't fit in a JavaScript number.

Shared shapes:
```jsonc
// author
{"id": "1", "name": "jane", "display_name": "Jane", "mention": "<@1>", "bot": false}
// message
{"id": "100", "content": "!hello", "channel_id": "10", "author": {…}}
```

### Handshake
The host speaks first; the Plugin must answer within 15 seconds or the Bot doesn't start.
```jsonc
// host → Plugin
{"type": "hello", "protocol": 1, "bot": {"name": "My Bot", "prefix": "!", "id": "42"}}
// Plugin → host
{"type": "register", "commands": [{"name": "hello", "help": "Says World"}], "events": ["mention", "message"]}
```
`commands` become Bot Commands (`help` is shown by `!help`). A name already used by a Reply or Cog stops the Bot
from starting. `events` lists the events the Plugin wants (`message`, `mention`), sorted; the host only sends those.
`bot.id` is `null` while the Bot isn't logged in (e.g. in `tinaja-bot check`).

### Events (host → Plugin)
```jsonc
{"type": "ready"}   // the Bot connected to Discord; may come again after a reconnect
{"type": "command", "name": "recap", "args": ["3"], "channel_id": "10", "author": {…}, "message": {…}}
{"type": "message", "message": {…}}                   // every message from a Member, Commands included
{"type": "mention", "message": {…}, "text": "hi"}     // the Bot was @mentioned without a Command; text has no mention
{"type": "result", "request_id": "1", "messages": [{…}]}   // answer to a history request
{"type": "error", "error": "…", "request_id": "1"}         // an action failed; request_id only for requests
{"type": "shutdown"}   // the Bot is stopping: exit soon, or the process is terminated after 5s
```
`args` are the words after the Command, split like discord.py does (`"quoted words"` stay together).
`mention` events need a `[mentions]` table in `bot.toml`. Messages from bots, including this Bot, are never sent.

### Actions (Plugin → host)
```jsonc
{"type": "send", "channel_id": "10", "content": "World"}
{"type": "send", "channel_id": "10", "content": "Hi!", "reply_to": "100"}   // a Discord reply to message 100
{"type": "react", "channel_id": "10", "message_id": "100", "emoji": "👍"}
{"type": "history", "request_id": "1", "channel_id": "10", "limit": 5}
```
`history` asks for the channel's latest `limit` Member messages, oldest first. The host answers with a `result`
carrying the same `request_id`, which the Plugin chooses (the SDKs count `"1"`, `"2"`, …). Other events may arrive
before the `result`.

Actions are fire and forget: the host only answers when one fails (an `error` event), e.g. an unknown `type` or a
channel the Bot can't see.

## Conformance
[`sdk/conformance/`](../sdk/conformance) holds recorded exchanges and a runner. Every SDK has a small Plugin that
implements the reference behaviour described there, and its CI job checks it against the recordings:
```bash
uv run python sdk/conformance/run.py -- ruby sdk/ruby/conformance/plugin.rb
```
