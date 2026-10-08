from tinaja_base.testing import fake_message, run_command

from cogs.hello import Hello


async def test_hello_answers_world():
    assert await run_command(Hello(), 'hello') == ['World']


async def test_mention_answers_world():
    message = fake_message('<@42> hi there')
    await Hello().on_mention(message, 'hi there')
    assert message.replies == ['World']
