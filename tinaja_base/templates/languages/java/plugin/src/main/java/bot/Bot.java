package bot;

import tinaja.Plugin;

/**
 * $bot_name's Commands and listeners. The bot runs this program and talks to it over stdin/stdout,
 * so log to System.err: anything printed to System.out must be protocol messages.
 */
public class Bot {
    static Plugin plugin() {
        return new Plugin()
                .command("hello", "Says World", ctx -> ctx.send("World"))
                .onMention((message, text) -> message.reply("World"));
    }

    public static void main(String[] args) throws Exception {
        plugin().run();
    }
}
