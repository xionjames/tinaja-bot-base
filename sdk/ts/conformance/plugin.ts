// The reference behaviour from sdk/conformance/README.md, in TypeScript (Node runs it by stripping the types)
import { Plugin, type Context, type Message } from '../index.js';

const plugin = new Plugin();

plugin.command('hello', { help: 'Says World' }, (ctx: Context) => ctx.send('World'));

plugin.command('echo', { help: 'Repeats what you say' }, (ctx: Context) => {
  ctx.send(ctx.args.length ? ctx.args.join(' ') : 'Nothing to echo');
});

plugin.command('recap', { help: 'The latest messages in the channel' }, async (ctx: Context) => {
  const messages = await ctx.history(Number(ctx.args[0] ?? 5));
  const lines = messages.map((m: Message) => `${m.author.displayName}: ${m.content}`);
  ctx.send(lines.length ? lines.join('\n') : 'Nothing to recap yet.');
});

plugin.onMention((message: Message, text: string) => message.reply(`You said: ${text}`));

plugin.onMessage((message: Message) => {
  if (message.content === 'ping') message.react('🏓');
});

await plugin.run();
