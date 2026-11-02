package tinaja;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** What a Command handler gets: who asked, where, and the words after the Command. */
public final class Context {
    private final String name;
    private final List<String> args;
    private final String channelId;
    private final Author author;
    private final Message message;
    private final Conn conn;

    Context(Map<?, ?> event, Conn conn) {
        this.name = Author.string(event, "name");
        this.args = new ArrayList<>();
        if (event.get("args") instanceof List<?> list) list.forEach(arg -> args.add(String.valueOf(arg)));
        this.channelId = Author.string(event, "channel_id");
        this.author = Author.from(event.get("author"));
        this.message = new Message(event.get("message") instanceof Map<?, ?> m ? m : Map.of(), conn);
        this.conn = conn;
    }

    public String name() { return name; }

    public List<String> args() { return args; }

    public String channelId() { return channelId; }

    public Author author() { return author; }

    public Message message() { return message; }

    public void send(String content) {
        conn.write(Plugin.sendAction(channelId, content));
    }

    public void reply(String content) {
        message.reply(content);
    }

    /** The channel's latest Member messages, oldest first. */
    public List<Message> history(int limit) throws IOException {
        return conn.history(channelId, limit);
    }
}
