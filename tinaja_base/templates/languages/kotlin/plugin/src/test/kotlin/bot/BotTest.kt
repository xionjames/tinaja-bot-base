package bot

import kotlin.test.Test
import kotlin.test.assertEquals
import tinaja.testing.Testing.fakeMessage
import tinaja.testing.Testing.runCommand
import tinaja.testing.Testing.runEvent

class BotTest {
    @Test
    fun helloAnswersWorld() {
        assertEquals(listOf("World"), runCommand(plugin(), "hello"))
    }

    @Test
    fun mentionAnswersWorld() {
        val actions = runEvent(plugin(), mapOf("type" to "mention", "message" to fakeMessage("<@42> hi"), "text" to "hi"), listOf())
        assertEquals(listOf(mapOf("type" to "send", "channel_id" to "10", "content" to "World", "reply_to" to "100")), actions)
    }
}
