package tinaja;

import static tinaja.testing.Testing.fakeAuthor;
import static tinaja.testing.Testing.fakeMessage;
import static tinaja.testing.Testing.runCommand;
import static tinaja.testing.Testing.runEvent;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

/** Plain-JDK tests, so the SDK builds without a build tool. Throws on the first failure. */
public class TinajaTest {
    static Plugin plugin() {
        return new Plugin()
                .command("hello", "Says World", ctx -> ctx.send("World, " + ctx.author().displayName()))
                .command("last", "", ctx -> ctx.reply(ctx.history(1).get(0).content()))
                .onMessage(message -> message.react("🏓"));
    }

    static void check(Object got, Object want) {
        if (!got.equals(want)) throw new AssertionError("got " + got + ", want " + want);
    }

    public static void main(String[] args) throws Exception {
        // runCommand returns what was sent
        check(runCommand(plugin(), List.of(), fakeAuthor("jane"), "hello"), List.of("World, jane"));
        // history comes from the given messages
        check(runCommand(plugin(), List.of(fakeMessage("old"), fakeMessage("new")), fakeAuthor("m"), "last"),
                List.of("new"));

        // runEvent returns actions
        Map<String, Object> ping = fakeMessage("ping");
        ping.put("id", "7");
        check(runEvent(plugin(), Map.of("type", "message", "message", ping), List.of()),
                List.of(Map.of("type", "react", "channel_id", "10", "message_id", "7", "emoji", "🏓")));

        // registration lists commands and events
        check(Json.write(plugin().registration()),
                "{\"type\":\"register\",\"commands\":[{\"name\":\"hello\",\"help\":\"Says World\"},"
                        + "{\"name\":\"last\",\"help\":\"\"}],\"events\":[\"message\"]}");

        // JSON round trips
        check(Json.parse("{\"a\": [1, 2.5, true, null, \"q\\\"\\u00e9\\n🏓\"]}"),
                Map.of("a", Arrays.asList(1L, 2.5, true, null, "q\"é\n🏓")));
        check(Json.write(Map.of("s", "a\"b\\c\n\u0001")), "{\"s\":\"a\\\"b\\\\c\\n\\u0001\"}");

        // a failing handler doesn't stop the Plugin
        Plugin failing = plugin().command("boom", "", ctx -> {
            throw new IllegalStateException("boom");
        });
        String input = String.join("\n",
                "{\"type\": \"hello\", \"protocol\": 1, \"bot\": {}}",
                "{\"type\": \"command\", \"name\": \"boom\", \"args\": [], \"channel_id\": \"10\"}",
                "{\"type\": \"command\", \"name\": \"hello\", \"args\": [], \"channel_id\": \"10\","
                        + " \"author\": {\"name\": \"jane\"}}");
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        PrintStream stderr = System.err;
        System.setErr(new PrintStream(new ByteArrayOutputStream()));
        try {
            failing.run(new ByteArrayInputStream(input.getBytes(StandardCharsets.UTF_8)), output);
        } finally {
            System.setErr(stderr);
        }
        List<String> lines = output.toString(StandardCharsets.UTF_8).lines().toList();
        check(lines.size(), 2);
        check(((Map<?, ?>) Json.parse(lines.get(1))).get("content"), "World, jane");

        System.out.println("ok   all Java SDK tests passed");
    }
}
