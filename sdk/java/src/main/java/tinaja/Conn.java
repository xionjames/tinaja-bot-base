package tinaja;

import java.io.IOException;
import java.util.List;
import java.util.Map;

/** Where a Plugin's actions go: the host over stdio, or a fake in tests (see tinaja.testing). */
public interface Conn {
    void write(Map<String, Object> action);

    List<Message> history(String channelId, int limit) throws IOException;
}
