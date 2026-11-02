package tinaja;

import java.util.LinkedHashMap;
import java.util.Map;

public final class Message {
    private final String id;
    private final String content;
    private final String channelId;
    private final Author author;
    private final Conn conn;

    public Message(Map<?, ?> data, Conn conn) {
        this.id = Author.string(data, "id");
        this.content = Author.string(data, "content");
        this.channelId = Author.string(data, "channel_id");
        this.author = Author.from(data.get("author"));
        this.conn = conn;
    }

    public String id() { return id; }

    public String content() { return content; }

    public String channelId() { return channelId; }

    public Author author() { return author; }

    public void reply(String content) {
        Map<String, Object> action = new LinkedHashMap<>();
        action.put("type", "send");
        action.put("channel_id", channelId);
        action.put("content", content);
        action.put("reply_to", id);
        conn.write(action);
    }

    public void react(String emoji) {
        Map<String, Object> action = new LinkedHashMap<>();
        action.put("type", "react");
        action.put("channel_id", channelId);
        action.put("message_id", id);
        action.put("emoji", emoji);
        conn.write(action);
    }
}
