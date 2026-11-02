# Conformance
Recorded exchanges of the [Plugin protocol](../../docs/protocol.md), and a runner that replays them against a Plugin:
```bash
uv run python sdk/conformance/run.py -- <command that starts the Plugin>
```

Every SDK keeps a `conformance/` Plugin with this reference behaviour, and its CI job runs it through the runner:
- Commands, registered in this order:
  - `hello` ("Says World"): sends `World`.
  - `echo` ("Repeats what you say"): sends the args joined by spaces, or `Nothing to echo`.
  - `recap` ("The latest messages in the channel"): `recap [n]`, `n` defaults to 5. Requests `n` messages of history
    and sends one `display_name: content` line per message, or `Nothing to recap yet.`
- `mention`: replies `You said: <text>` to the message.
- `message`: reacts `🏓` to messages whose content is exactly `ping`.
- `error` events go to stderr; unknown events and fields are ignored; `shutdown` exits with status 0.
- `request_id`s count up from `"1"`.

Events that arrive while a handler waits for a `result` are handled after that handler finishes, in order.
