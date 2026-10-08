from tinaja_base.cogs.glossary import Glossary
from tinaja_base.context import Context
from tinaja_base.testing import run_command

CONTEXT = Context.from_markdown(
    '# Bot\n\n## Language\n\n**Member**:\nA person.\n_Avoid_: User\n\n**Online member**:\nA Member who is online.\n'
)


async def test_lists_terms():
    assert await run_command(Glossary(CONTEXT), 'glossary') == ['Glossary terms: Member, Online member']


async def test_defines_a_term_of_several_words():
    sent = await run_command(Glossary(CONTEXT), 'glossary', 'online', 'MEMBER')
    assert sent == ['**Online member**: A Member who is online.']


async def test_includes_words_to_avoid():
    assert await run_command(Glossary(CONTEXT), 'glossary', 'member') == ['**Member**: A person.\n_Avoid_: User']


async def test_unknown_term():
    assert await run_command(Glossary(CONTEXT), 'glossary', 'guild') == ['@member "guild" is not in the glossary']


async def test_empty_glossary():
    assert await run_command(Glossary(Context()), 'glossary') == ['The glossary is empty.']
