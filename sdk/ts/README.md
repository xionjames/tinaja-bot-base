# tinaja (TypeScript / JavaScript SDK)
Write the Commands and listeners of a [tinaja-bot-base](../..) Bot in TypeScript or JavaScript. It has no
dependencies and needs Node 22.6 or newer, or 24.2 or newer to run `.ts` files directly. `tinaja-bot new "My Bot" --lang ts`
sets everything up. To add it by hand:
```bash
npm install git+https://github.com/xionjames/tinaja-bot-base.git#main
```
```ts
import { Plugin } from 'tinaja';

const plugin = new Plugin();
plugin.command('hello', { help: 'Says World' }, (ctx) => ctx.send('World'));  // ctx.args, ctx.author, ctx.reply
plugin.command('recap', async (ctx) => ctx.send((await ctx.history(5)).map((m) => m.content).join('\n')));
plugin.onMessage((message) => { if (message.content.includes('bot')) message.react('👀'); });
plugin.onMention((message, text) => message.reply(`You said: ${text}`));
await plugin.run();
```
- `Context`: `name`, `args`, `channelId`, `author`, `message`, `send(text)`, `reply(text)`, `history(limit = 20)`
  (a Promise)
- `Message`: `id`, `content`, `channelId`, `author`, `reply(text)`, `react(emoji)`
- `Author`: `id`, `name`, `displayName`, `mention`, `bot`
- `plugin.send(channelId, text)` and `plugin.history(channelId, limit)` work outside handlers too.

Handlers can be async and run one at a time; events that arrive meanwhile wait their turn. A handler that throws is
logged to stderr and the Plugin keeps running.

## Testing
```ts
import { fakeMessage, runCommand, runEvent } from 'tinaja/testing';

await runCommand(plugin, 'hello');                                          // ['World']
await runCommand(plugin, 'recap', [], { history: [fakeMessage('hi')] });     // history comes from the list
await runEvent(plugin, { type: 'message', message: fakeMessage('bot?') });   // the actions, as protocol objects
```

## Develop
From the repository root (the root `package.json` is this SDK's package):
```bash
npm test
uv run python sdk/conformance/run.py -- node sdk/ts/conformance/plugin.ts
```
