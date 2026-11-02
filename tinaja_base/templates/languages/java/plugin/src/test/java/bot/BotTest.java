package bot;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static tinaja.testing.Testing.fakeMessage;
import static tinaja.testing.Testing.runCommand;
import static tinaja.testing.Testing.runEvent;

import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class BotTest {
    @Test
    void helloAnswersWorld() throws Exception {
        assertEquals(List.of("World"), runCommand(Bot.plugin(), "hello"));
    }

    @Test
    void mentionAnswersWorld() throws Exception {
        var actions = runEvent(Bot.plugin(), Map.of("type", "mention", "message", fakeMessage("<@42> hi"), "text", "hi"), List.of());
        assertEquals(List.of(Map.of("type", "send", "channel_id", "10", "content", "World", "reply_to", "100")), actions);
    }
}
