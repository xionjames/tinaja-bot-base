# Tinaja Bot Base

A Python framework to build Discord bots for a community server: each bot is a configuration file, a glossary and the code of its Commands, in Python or, through a Plugin, in another language.

## Language

**Bot**:
One Discord bot built on the framework: its bot.toml, CONTEXT.md and Cogs, usually in a repo of its own.
_Avoid_: App, client

**Server**:
A Discord guild the Bot has joined.
_Avoid_: Guild (except when talking about the Discord library), channel

**Member**:
A person's Discord account that belongs to a Server. Bot accounts are not Members.
_Avoid_: User

**Command**:
A prefixed message a Member sends to ask the Bot for something, e.g. `!hello`.
_Avoid_: Slash command (the framework doesn't use them)

**Reply**:
A Command defined only by its text in bot.toml, with no Python code.

**Cog**:
A discord.py class in a Bot's cogs folder that groups Commands and listeners; the framework loads every one it finds.
_Avoid_: Plugin (that's the other-language kind), extension

**Plugin**:
A long-running process in any language (Ruby, TypeScript, Go, Java...) that adds Commands and listeners to a Bot by
speaking the Plugin protocol over stdin/stdout; declared under `[plugins.<name>]` in bot.toml.
_Avoid_: Script, external command, extension

**SDK**:
A library for one language, in the framework's sdk/ folder, that implements the Plugin protocol so a Plugin only
writes handlers.
_Avoid_: Client library, binding

**Mention**:
A message that @mentions the Bot without being a Command; Cogs receive it as an on_mention event.

**Glossary term**:
A word of the Server's language defined in CONTEXT.md, which Members can ask about with `!glossary`.
