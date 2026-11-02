import assert from 'node:assert/strict';
import { test } from 'node:test';
import { fakeMessage, runCommand, runEvent } from 'tinaja/testing';
import { plugin } from '../bot.ts';

test('hello answers World', async () => {
  assert.deepEqual(await runCommand(plugin, 'hello'), ['World']);
});

test('mention answers World', async () => {
  const actions = await runEvent(plugin, { type: 'mention', message: fakeMessage('<@42> hi', { id: '5' }), text: 'hi' });
  assert.deepEqual(actions, [{ type: 'send', channel_id: '10', content: 'World', reply_to: '5' }]);
});
