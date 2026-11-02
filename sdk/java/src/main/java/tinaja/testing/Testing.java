package tinaja.testing;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import tinaja.Conn;
import tinaja.Json;
import tinaja.Message;
import tinaja.Plugin;

/** Run a Plugin's handlers without a Bot: what they send is recorded, history comes from a list. */
public final class Testing {
    private Testing() {}

    /** Records every action as a protocol message and answers history from messages (oldest first). */
    public static final class FakeConn implements Conn {
        public final List<Map<String, Object>> actions = new ArrayList<>();
        public final List<Map<String, Object>> messages;

        public FakeConn(List<Map<String, Object>> messages) {
            this.messages = messages;
        }

        @Override
        public void write(Map<String, Object> action) {
            actions.add(action);
        }

        @Override
        public List<Message> history(String channelId, int limit) {
            List<Message> result = new ArrayList<>();
            for (Map<String, Object> data : messages.subList(Math.max(0, messages.size() - limit), messages.size())) {
                result.add(new Message(data, this));
            }
            return result;
        }
    }

    public static Map<String, Object> fakeAuthor(String name) {
        Map<String, Object> author = new LinkedHashMap<>();
        author.put("id", "1");
        author.put("name", name);
        author.put("display_name", name);
        author.put("mention", "<@1>");
        author.put("bot", false);
        return author;
    }

    /** Message 100 in channel 10, written by "member". */
    public static Map<String, Object> fakeMessage(String content) {
        Map<String, Object> message = new LinkedHashMap<>();
        message.put("id", "100");
        message.put("content", content);
        message.put("channel_id", "10");
        message.put("author", fakeAuthor("member"));
        return message;
    }

    /** Dispatch one protocol event, as a Map or a JSON string, and return the actions it caused. */
    public static List<Map<String, Object>> runEvent(Plugin plugin, Object event, List<Map<String, Object>> history)
            throws Exception {
        FakeConn conn = new FakeConn(history);
        Object parsed = event instanceof String json ? Json.parse(json) : event;
        plugin.dispatch(conn, (Map<?, ?>) parsed);
        return conn.actions;
    }

    /** Run a Command like the Bot would, returning the text it sent (sends and replies). */
    public static List<String> runCommand(Plugin plugin, String name, String... args) throws Exception {
        return runCommand(plugin, List.of(), fakeAuthor("member"), name, args);
    }

    public static List<String> runCommand(
            Plugin plugin, List<Map<String, Object>> history, Map<String, Object> author, String name, String... args)
            throws Exception {
        Map<String, Object> message = fakeMessage(("!" + name + " " + String.join(" ", args)).trim());
        message.put("author", author);
        Map<String, Object> event = new LinkedHashMap<>();
        event.put("type", "command");
        event.put("name", name);
        event.put("args", List.of(args));
        event.put("channel_id", "10");
        event.put("author", author);
        event.put("message", message);
        List<String> sent = new ArrayList<>();
        for (Map<String, Object> action : runEvent(plugin, event, history)) {
            if ("send".equals(action.get("type"))) sent.add((String) action.get("content"));
        }
        return sent;
    }
}
