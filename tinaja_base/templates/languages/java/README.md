# $bot_name
A Discord bot built on [tinaja-bot-base](https://github.com/xionjames/tinaja-bot-base), written in Java.

The bot runs on a small Python host that connects to Discord. Your code is a Java **plugin**: the host starts the
program built from `plugin/` and passes it Commands, messages and mentions. The host speaks
[the plugin protocol](https://github.com/xionjames/tinaja-bot-base/blob/main/docs/protocol.md) with it over
stdin/stdout, and the `tinaja` SDK handles that for you. The SDK has no dependencies, and Gradle gets it from
[JitPack](https://jitpack.io), which builds it from the tinaja-bot-base repo.

## Project layout
- `bot.toml`: name, command prefix, intents, plain-text replies, @mention behaviour and the plugin
- `CONTEXT.md`: the glossary of the server's language, answered by `!glossary [term]`
- `plugin/`: the Java code of the bot (`src/main/java/bot/Bot.java`), its Gradle build and tests
- `.env`: the bot token (never commit it; copy `env.sample`). The plugin never sees it.

## Write commands
```java
new Plugin()
        .command("roll", "Rolls a die", ctx -> ctx.send(String.valueOf(new Random().nextInt(6) + 1)))
        .command("recap", "The latest messages", ctx -> {     // ctx.args(): the words after the Command
            for (Message m : ctx.history(5)) ctx.send(m.author().displayName() + ": " + m.content());
        })
        .onMessage(message -> { if (message.content().contains("hola")) message.react("👋"); })
        .onMention((message, text) -> message.reply("You said: " + text));
```
The plugin is one long-running process, so fields keep state between messages. A handler that throws is logged
and the plugin keeps running. Add libraries to `plugin/build.gradle.kts`. Log to `System.err`, because
`System.out` is reserved for the protocol.

## Run manually
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/), a JDK (21 or newer) and
  [Gradle](https://gradle.org/install/), then install the dependencies
```bash
uv sync
(cd plugin && gradle wrapper)   # optional: adds ./gradlew, so others don't need Gradle installed
```
- Create a new `.env` file using `env.sample` as a template to set the required credentials.
- Build the plugin, after every change, then run the bot
```bash
(cd plugin && gradle installDist)
uv run tinaja-bot run
```

## Run tests
```bash
cd plugin && gradle test
```

## Docker
```bash
uv run tinaja-bot check                # is the bot ready to build? (build runs this first; needs the plugin built)
uv run tinaja-bot build                # docker build, tagged ghcr.io/<owner>/<repo>:latest and :<git sha>
docker run -it --env-file .env ghcr.io/<owner>/<repo>:latest
uv run tinaja-bot publish              # docker push; first: echo $CR_PAT | docker login ghcr.io -u <user> --password-stdin
```
The image builds the plugin itself. Pushing to `main` on GitHub runs `.github/workflows/build-and-push.yaml`.
It tests and builds the plugin and runs `tinaja-bot check`, and only then publishes a multi-arch image to
`ghcr.io/<owner>/<repo>`.
