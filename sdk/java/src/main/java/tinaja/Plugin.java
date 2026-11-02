package tinaja;

import java.io.BufferedReader;
import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * SDK for tinaja-bot-base Plugins: a Bot's Commands and listeners written in Java (or Kotlin). The Bot (a Python host)
 * runs this program and talks to it over stdin/stdout, see docs/protocol.md.
 */
public final class Plugin {
    public static final int PROTOCOL = 1;

    @FunctionalInterface
    public interface CommandHandler {
        void handle(Context ctx) throws Exception;
    }

    @FunctionalInterface
    public interface MessageHandler {
        void handle(Message message) throws Exception;
    }

    @FunctionalInterface
    public interface MentionHandler {
        void handle(Message message, String text) throws Exception;
    }

    private record Command(String help, CommandHandler handler) {}

    private final Map<String, Command> commands = new LinkedHashMap<>(); // in registration order
    private final List<MessageHandler> messageHandlers = new ArrayList<>();
    private final List<MentionHandler> mentionHandlers = new ArrayList<>();
    private Map<?, ?> bot = Map.of();
    private Conn conn;

    /** handler runs for every !name; help is shown by !help. */
    public Plugin command(String name, String help, CommandHandler handler) {
        commands.put(name, new Command(help, handler));
        return this;
    }

    /** handler runs for every message from a Member, Commands included. */
    public Plugin onMessage(MessageHandler handler) {
        messageHandlers.add(handler);
        return this;
    }

    /** handler runs when the Bot is @mentioned without a Command; needs [mentions] in bot.toml. */
    public Plugin onMention(MentionHandler handler) {
        mentionHandlers.add(handler);
        return this;
    }

    /** The hello's bot info: name, prefix, id. */
    public Map<?, ?> bot() { return bot; }

    public void send(String channelId, String content) {
        conn.write(sendAction(channelId, content));
    }

    public List<Message> history(String channelId, int limit) throws IOException {
        return conn.history(channelId, limit);
    }

    public Map<String, Object> registration() {
        List<Object> commandList = new ArrayList<>();
        commands.forEach((name, command) -> {
            Map<String, Object> info = new LinkedHashMap<>();
            info.put("name", name);
            info.put("help", command.help());
            commandList.add(info);
        });
        List<Object> events = new ArrayList<>(); // sorted, as the protocol asks
        if (!mentionHandlers.isEmpty()) events.add("mention");
        if (!messageHandlers.isEmpty()) events.add("message");
        Map<String, Object> registration = new LinkedHashMap<>();
        registration.put("type", "register");
        registration.put("commands", commandList);
        registration.put("events", events);
        return registration;
    }

    /** Serve the host over stdin/stdout until it says shutdown or closes stdin. */
    public void run() throws IOException {
        run(System.in, new FileOutputStream(FileDescriptor.out));
    }

    public void run(InputStream in, OutputStream out) throws IOException {
        StdioConn stdio = new StdioConn(in, out);
        Map<?, ?> event;
        while ((event = stdio.read()) != null) {
            if ("shutdown".equals(event.get("type"))) return;
            handle(stdio, event);
        }
    }

    /** Dispatch one event, logging handler errors: one failing handler mustn't stop the Plugin. */
    private void handle(Conn conn, Map<?, ?> event) {
        try {
            dispatch(conn, event);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /** Handle one protocol event, letting handler errors through. */
    public void dispatch(Conn conn, Map<?, ?> event) throws Exception {
        this.conn = conn;
        Object type = event.get("type");
        if ("hello".equals(type)) {
            bot = event.get("bot") instanceof Map<?, ?> m ? m : Map.of();
            conn.write(registration());
        } else if ("command".equals(type)) {
            Command command = commands.get(event.get("name"));
            if (command != null) command.handler().handle(new Context(event, conn));
        } else if ("message".equals(type)) {
            for (MessageHandler handler : messageHandlers) handler.handle(new Message(messageOf(event), conn));
        } else if ("mention".equals(type)) {
            String text = event.get("text") instanceof String s ? s : "";
            for (MentionHandler handler : mentionHandlers) handler.handle(new Message(messageOf(event), conn), text);
        } else if ("error".equals(type)) {
            System.err.println("tinaja: the host reported an error: " + event.get("error"));
        }
        // anything else (ready, future events) needs no answer
    }

    private static Map<?, ?> messageOf(Map<?, ?> event) {
        return event.get("message") instanceof Map<?, ?> m ? m : Map.of();
    }

    static Map<String, Object> sendAction(String channelId, String content) {
        Map<String, Object> action = new LinkedHashMap<>();
        action.put("type", "send");
        action.put("channel_id", channelId);
        action.put("content", content);
        return action;
    }
}

/** JSON lines over stdin/stdout. */
final class StdioConn implements Conn {
    private final BufferedReader in;
    private final PrintStream out;
    private final Deque<Map<?, ?>> pending = new ArrayDeque<>(); // events that arrived while waiting for a result
    private int nextId = 1;

    StdioConn(InputStream in, OutputStream out) {
        this.in = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8));
        this.out = new PrintStream(out, true, StandardCharsets.UTF_8);
    }

    @Override
    public void write(Map<String, Object> action) {
        out.print(Json.write(action) + "\n");
        out.flush();
    }

    /** The next event, or null when the host closed stdin. */
    Map<?, ?> read() throws IOException {
        return pending.isEmpty() ? readLine() : pending.poll();
    }

    private Map<?, ?> readLine() throws IOException {
        String line;
        while ((line = in.readLine()) != null) {
            if (!line.isBlank() && Json.parse(line) instanceof Map<?, ?> event) return event;
        }
        return null;
    }

    @Override
    public List<Message> history(String channelId, int limit) throws IOException {
        String requestId = String.valueOf(nextId++);
        Map<String, Object> request = new LinkedHashMap<>();
        request.put("type", "history");
        request.put("request_id", requestId);
        request.put("channel_id", channelId);
        request.put("limit", limit);
        write(request);
        Map<?, ?> event;
        while ((event = readLine()) != null) {
            Object type = event.get("type");
            if (requestId.equals(event.get("request_id")) && ("result".equals(type) || "error".equals(type))) {
                if ("error".equals(type)) throw new IOException(String.valueOf(event.get("error")));
                List<Message> messages = new ArrayList<>();
                if (event.get("messages") instanceof List<?> list) {
                    for (Object data : list) messages.add(new Message((Map<?, ?>) data, this));
                }
                return messages;
            }
            pending.add(event);
        }
        throw new IOException("the host closed the connection");
    }
}
