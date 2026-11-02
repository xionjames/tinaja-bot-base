# $bot_name
A Discord bot built on [tinaja-bot-base](https://github.com/xionjames/tinaja-bot-base), written in TypeScript.

The bot runs on a small Python host that connects to Discord. Your code is a TypeScript **plugin**: the host starts
`plugin/bot.ts` and passes it Commands, messages and mentions. The host speaks
[the plugin protocol](https://github.com/xionjames/tinaja-bot-base/blob/main/docs/protocol.md) with it over
stdin/stdout, and the `tinaja` package handles that for you. Node (24.2 or newer) runs the `.ts` files directly by
stripping their types, so there's no build step. Use type annotations only: no `enum` or `namespace`.

## Project layout
- `bot.toml`: name, command prefix, intents, plain-text replies, @mention behaviour and the plugin
- `CONTEXT.md`: the glossary of the server's language, answered by `!glossary [term]`
- `plugin/`: the TypeScript code of the bot (`bot.ts`), its `package.json` and tests
- `.env`: the bot token (never commit it; copy `env.sample`). The plugin never sees it.

## Write commands
```ts
plugin.command('roll', { help: 'Rolls a die' }, (ctx) => ctx.send(String(1 + Math.floor(Math.random() * 6))));

plugin.command('recap', async (ctx) => {                     // ctx.args are the words after the Command
  const messages = await ctx.history(Number(ctx.args[0] ?? 5));  // latest Member messages, oldest first
  ctx.send(messages.map((m) => `${m.author.displayName}: ${m.content}`).join('\n'));
});

plugin.onMessage((message) => { if (message.content.includes('hola')) message.react('👋'); });
plugin.onMention((message, text) => message.reply(`You said: ${text}`));
```
The plugin is one long-running process, so plain variables keep state between messages. Use any npm package:
`cd plugin && npm install <package>`. Log with `console.error`, because stdout is reserved for the protocol.

## Run manually
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Node 24, then install the dependencies
```bash
uv sync
(cd plugin && npm install)
```
- Create a new `.env` file using `env.sample` as a template to set the required credentials.
- Run the bot
```bash
uv run tinaja-bot run
```

## Run tests
```bash
cd plugin && npm test
```
Optionally type-check with `npx -p typescript tsc` in `plugin/`.

## Docker
```bash
uv run tinaja-bot check                # is the bot ready to build? (build runs this first)
uv run tinaja-bot build                # docker build, tagged ghcr.io/<owner>/<repo>:latest and :<git sha>
docker run -it --env-file .env ghcr.io/<owner>/<repo>:latest
uv run tinaja-bot publish              # docker push; first: echo $CR_PAT | docker login ghcr.io -u <user> --password-stdin
```
Pushing to `main` on GitHub runs `.github/workflows/build-and-push.yaml`. It tests the plugin and runs
`tinaja-bot check`, and only then publishes a multi-arch image to `ghcr.io/<owner>/<repo>`.
