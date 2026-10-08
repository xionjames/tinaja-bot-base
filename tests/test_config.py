import pytest

from tinaja_base.config import Config, Intents


@pytest.fixture(autouse=True)
def token(monkeypatch):
    monkeypatch.setenv('DISCORD_BOT_TOKEN', 'abc')


def write(tmp_path, text):
    path = tmp_path / 'bot.toml'
    path.write_text(text)
    return path


def test_defaults_for_an_empty_file(tmp_path):
    config = Config.load(write(tmp_path, ''))
    assert config == Config(token='abc', root=tmp_path)
    assert config.intents == Intents(message_content=True, members=False, presences=False)
    assert not config.mentions


def test_reads_bot_toml(tmp_path):
    config = Config.load(
        write(
            tmp_path,
            """
name = "Hello Bot"
prefix = "?"
cogs_dir = "commands"

[intents]
members = true

[replies]
ping = "pong"
fallback = "unknown"

[mentions]
as_prefix = true
reply = "hi"
""",
        )
    )
    assert config.name == 'Hello Bot'
    assert config.prefix == '?'
    assert config.intents == Intents(message_content=True, members=True)
    assert config.replies == {'ping': 'pong'}  # fallback is not a Command
    assert config.reply_fallback == 'unknown'
    assert (config.mentions, config.mention_prefix, config.mention_reply) == (True, True, 'hi')


def test_paths_resolve_against_the_toml_folder(tmp_path, monkeypatch):
    monkeypatch.chdir('/')
    config = Config.load(write(tmp_path, 'cogs_dir = "commands"'))
    assert config.cogs_path == tmp_path / 'commands'
    assert config.context_path == tmp_path / 'CONTEXT.md'


def test_empty_mentions_table_enables_mentions(tmp_path):
    config = Config.load(write(tmp_path, '[mentions]'))
    assert config.mentions and not config.mention_prefix and config.mention_reply is None


def test_requires_token(tmp_path, monkeypatch):
    monkeypatch.delenv('DISCORD_BOT_TOKEN')
    with pytest.raises(ValueError):
        Config.load(write(tmp_path, ''))


def test_reads_token_from_dotenv_next_to_the_toml(tmp_path, monkeypatch):
    monkeypatch.delenv('DISCORD_BOT_TOKEN')
    (tmp_path / '.env').write_text('DISCORD_BOT_TOKEN=from-dotenv\n')
    assert Config.load(write(tmp_path, '')).token == 'from-dotenv'
