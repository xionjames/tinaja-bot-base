from pathlib import Path

from tinaja_base.context import Context, Term

TINAJA = Path(__file__).parent / 'fixtures' / 'tinaja_context.md'


def test_parses_tinaja_context():
    context = Context.from_file(TINAJA)
    assert context.title == 'Tinaja Bot'
    assert context.description.startswith('A Discord bot for the TINAJA')
    assert len(context.terms) == 7
    assert context.lookup('member') == Term(
        'Member', "A person's Discord account that belongs to a Server. Bot accounts are not Members.", 'User'
    )


def test_lookup_ignores_case_and_spaces():
    context = Context.from_file(TINAJA)
    assert context.lookup('  ONLINE member ').name == 'Online member'


def test_term_without_avoid():
    context = Context.from_file(TINAJA)
    term = context.lookup('exercism profile')
    assert term.avoid is None
    assert 'exercism.org' in term.definition


def test_definition_on_the_term_line_and_across_lines():
    context = Context.from_markdown('# T\n\n## Language\n\n**Cog**: A class\nthat groups Commands.\n')
    assert context.lookup('cog').definition == 'A class that groups Commands.'


def test_missing_file_is_empty(tmp_path):
    assert Context.from_file(tmp_path / 'CONTEXT.md') == Context()
