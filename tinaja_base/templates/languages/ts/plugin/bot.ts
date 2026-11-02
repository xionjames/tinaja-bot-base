// $bot_name's Commands and listeners. The bot runs this file and talks to it over stdin/stdout,
// so log with console.error (stderr): anything printed to stdout must be protocol messages.
import { Plugin } from 'tinaja';

export const plugin = new Plugin();

plugin.command('hello', { help: 'Says World' }, (ctx) => ctx.send('World'));

plugin.onMention((message) => message.reply('World'));

if (import.meta.main) await plugin.run();
