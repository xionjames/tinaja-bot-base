import re
from dataclasses import dataclass, field
from pathlib import Path

_TERM = re.compile(r'^\*\*(.+?)\*\*:\s*(.*)$')
_AVOID = re.compile(r'^_Avoid_:\s*(.*)$')


@dataclass(frozen=True)
class Term:
    name: str
    definition: str
    avoid: str | None = None


@dataclass(frozen=True)
class Context:
    """The bot's domain language, read from a CONTEXT.md file"""

    title: str = ''
    description: str = ''
    terms: dict[str, Term] = field(default_factory=dict)

    def lookup(self, name):
        """Find a Term by name, ignoring case; None when it isn't defined"""
        return self.terms.get(name.strip().casefold())

    @classmethod
    def from_file(cls, path):
        path = Path(path)
        if not path.is_file():
            return cls()
        return cls.from_markdown(path.read_text(encoding='utf-8'))

    @classmethod
    def from_markdown(cls, text):
        title = ''
        description = []
        terms = {}
        current = None  # [name, definition lines, avoid] of the Term being read
        in_intro = False

        def finish():
            if current is not None:
                name, lines, avoid = current
                terms[name.casefold()] = Term(name, ' '.join(lines), avoid)

        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith('# ') and not title:
                title = line[2:].strip()
                in_intro = True
            elif line.startswith('#'):
                in_intro = False
            elif in_intro:
                if line:
                    description.append(line)
            elif match := _TERM.match(line):
                finish()
                current = [match[1].strip(), [match[2]] if match[2] else [], None]
            elif current is not None and (match := _AVOID.match(line)):
                current[2] = match[1].strip()
            elif current is not None and line:
                current[1].append(line)
        finish()
        return cls(title, ' '.join(description), terms)
