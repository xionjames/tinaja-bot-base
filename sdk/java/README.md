# tinaja (Java SDK, also for Kotlin)
Write the Commands and listeners of a [tinaja-bot-base](../..) Bot in Java or Kotlin. It has no dependencies (it even
brings its own small JSON reader) and needs Java 21 or newer. `tinaja-bot new "My Bot" --lang java` (or `kotlin`)
sets everything up. To add it by hand with Gradle, through [JitPack](https://jitpack.io):
```kotlin
repositories { maven("https://jitpack.io") }
dependencies { implementation("com.github.xionjames:tinaja-bot-base:main-SNAPSHOT") }  // or a tag or commit
```
```java
new Plugin()
        .command("hello", "Says World", ctx -> ctx.send("World"))       // ctx.args(), ctx.author(), ctx.reply()
        .command("recap", "The latest messages", ctx -> ctx.history(5).forEach(m -> ctx.send(m.content())))
        .onMessage(message -> { if (message.content().contains("bot")) message.react("👀"); })
        .onMention((message, text) -> message.reply("You said: " + text))
        .run();
```
- `Context`: `name()`, `args()`, `channelId()`, `author()`, `message()`, `send(text)`, `reply(text)`, `history(limit)`
- `Message`: `id()`, `content()`, `channelId()`, `author()`, `reply(text)`, `react(emoji)`
- `Author` (a record): `id()`, `name()`, `displayName()`, `mention()`, `bot()`
- `plugin.send(channelId, text)` and `plugin.history(channelId, limit)`, from the thread that runs the handlers

Handlers run one at a time and may throw: the exception is logged to stderr and the Plugin keeps running. A Plugin's
stdout is the protocol, so start it with Gradle's `installDist` script (or `java -cp ...`), never `gradle run`.

## Testing
Works with any test framework:
```java
import static tinaja.testing.Testing.*;

runCommand(plugin, "hello");                                              // ["World"]
runCommand(plugin, List.of(fakeMessage("hi")), fakeAuthor("jane"), "recap", "5");   // history comes from the list
runEvent(plugin, Map.of("type", "message", "message", fakeMessage("bot?")), List.of()); // the actions, as maps
```

## Develop
No build tool, on purpose:
```bash
javac -Xlint:all -Werror --release 21 -d build/classes $(find src/main/java -name '*.java')
javac --release 21 -cp build/classes -d build/test src/test/java/tinaja/TinajaTest.java conformance/ConformancePlugin.java
java -cp build/classes:build/test tinaja.TinajaTest
uv run python ../conformance/run.py -- java -cp build/classes:build/test ConformancePlugin
```
