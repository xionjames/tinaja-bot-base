// $bot_name's Commands and listeners. The bot runs this program and talks to it over stdin/stdout,
// so log to System.err: anything printed to System.out must be protocol messages.
package bot

import tinaja.Plugin

fun plugin(): Plugin = Plugin()
    .command("hello", "Says World") { ctx -> ctx.send("World") }
    .onMention { message, _ -> message.reply("World") }

fun main() {
    plugin().run()
}
