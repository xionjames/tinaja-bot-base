import java.util.List;
import tinaja.Message;
import tinaja.Plugin;

/** The reference behaviour from sdk/conformance/README.md */
public class ConformancePlugin {
    public static void main(String[] args) throws Exception {
        new Plugin()
                .command("hello", "Says World", ctx -> ctx.send("World"))
                .command("echo", "Repeats what you say", ctx -> ctx.send(
                        ctx.args().isEmpty() ? "Nothing to echo" : String.join(" ", ctx.args())))
                .command("recap", "The latest messages in the channel", ctx -> {
                    int count = ctx.args().isEmpty() ? 5 : Integer.parseInt(ctx.args().get(0));
                    List<String> lines = ctx.history(count).stream()
                            .map((Message m) -> m.author().displayName() + ": " + m.content())
                            .toList();
                    ctx.send(lines.isEmpty() ? "Nothing to recap yet." : String.join("\n", lines));
                })
                .onMention((message, text) -> message.reply("You said: " + text))
                .onMessage(message -> {
                    if (message.content().equals("ping")) message.react("🏓");
                })
                .run();
    }
}
