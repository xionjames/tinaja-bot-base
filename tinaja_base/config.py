import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Intents:
    message_content: bool = True  # privileged: also enable it in the Discord Developer Portal
    members: bool = False
    presences: bool = False


@dataclass(frozen=True)
class Config:
    token: str
    name: str = 'Bot'
    prefix: str = '!'
    root: Path = Path('.')
    cogs_dir: str = 'cogs'
    context_file: str = 'CONTEXT.md'
    intents: Intents = field(default_factory=Intents)
    replies: dict[str, str] = field(default_factory=dict)
    reply_fallback: str | None = None  # [replies] fallback: the answer to an unknown Command
    mentions: bool = False  # True when bot.toml has a [mentions] table
    mention_prefix: bool = False
    mention_reply: str | None = None

    @property
    def cogs_path(self):
        return self.root / self.cogs_dir

    @property
    def context_path(self):
        return self.root / self.context_file

    @classmethod
    def load(cls, path='bot.toml', require_token=True):
        """Read bot.toml, plus the token from the environment or a .env file next to it"""
        path = Path(path).resolve()
        with path.open('rb') as f:
            data = tomllib.load(f)

        load_dotenv(path.parent / '.env')
        token = os.getenv('DISCORD_BOT_TOKEN')
        if token is None and require_token:
            raise ValueError('No token found. Make sure to set the DISCORD_BOT_TOKEN environment variable.')

        mentions = data.get('mentions')
        replies = dict(data.get('replies', {}))
        fallback = replies.pop('fallback', None)  # reserved: answers unknown Commands instead of being one
        return cls(
            token=token or '',
            name=data.get('name', cls.name),
            prefix=data.get('prefix', cls.prefix),
            root=path.parent,
            cogs_dir=data.get('cogs_dir', cls.cogs_dir),
            context_file=data.get('context_file', cls.context_file),
            intents=Intents(**data.get('intents', {})),
            replies=replies,
            reply_fallback=fallback,
            mentions=mentions is not None,
            mention_prefix=(mentions or {}).get('as_prefix', False),
            mention_reply=(mentions or {}).get('reply'),
        )
