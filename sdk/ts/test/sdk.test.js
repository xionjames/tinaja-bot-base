import assert from 'node:assert/strict';
import { PassThrough } from 'node:stream';
import { test } from 'node:test';
import { Plugin } from '../index.js';
import { fakeAuthor, fakeMessage, runCommand, runEvent } from '../testing.js';

function makePlugin() {
  return new Plugin()
    .command('hello', { help: 'Says World' }, (ctx) => ctx.send(`World, ${ctx.author.displayName}`))
    .command('last', async (ctx) => ctx.reply((await ctx.history(1))[0].content))
    .onMessage((message) => message.react('🏓'));
}

test('runCommand returns what was sent', async () => {
  assert.deepEqual(await runCommand(makePlugin(), 'hello', [], { author: fakeAuthor('jane') }), ['World, jane']);
});

test('history comes from the given messages', async () => {
  const history = [fakeMessage('old'), fakeMessage('new')];
  assert.deepEqual(await runCommand(makePlugin(), 'last', [], { history }), ['new']);
});

test('runEvent returns actions', async () => {
  const actions = await runEvent(makePlugin(), { type: 'message', message: fakeMessage('ping', { id: '7' }) });
  assert.deepEqual(actions, [{ type: 'react', channel_id: '10', message_id: '7', emoji: '🏓' }]);
});

test('registration lists commands and events', () => {
  assert.deepEqual(makePlugin().registration(), {
    type: 'register',
    commands: [
      { name: 'hello', help: 'Says World' },
      { name: 'last', help: '' },
    ],
    events: ['message'],
  });
});

test('a failing handler does not stop the plugin', async (t) => {
  const plugin = makePlugin().command('boom', () => {
    throw new Error('boom');
  });
  const errors = t.mock.method(console, 'error', () => {});
  const input = new PassThrough();
  const output = new PassThrough();
  const running = plugin.run(input, output);
  input.end(
    [
      { type: 'hello', protocol: 1, bot: {} },
      { type: 'command', name: 'boom', args: [], channel_id: '10' },
      { type: 'command', name: 'hello', args: [], channel_id: '10', author: { name: 'jane' } },
    ]
      .map((event) => JSON.stringify(event) + '\n')
      .join(''),
  );
  await running;
  const lines = output.read().toString().trim().split('\n').map((line) => JSON.parse(line));
  assert.deepEqual(lines.map((line) => line.type), ['register', 'send']);
  assert.equal(lines[1].content, 'World, jane');
  assert.equal(errors.mock.callCount(), 1);
});
