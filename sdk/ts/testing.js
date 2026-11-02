// Run a Plugin's handlers without a Bot: what they send is recorded, history comes from a list
import { Message } from './index.js';

export function fakeAuthor(name = 'member', { id = '1', bot = false } = {}) {
  return { id, name, display_name: name, mention: `<@${id}>`, bot };
}

export function fakeMessage(content, { author, id = '100', channelId = '10' } = {}) {
  return { id, content, channel_id: channelId, author: author ?? fakeAuthor() };
}

export class FakeConnection {
  constructor(history = []) {
    this.actions = []; // every action the Plugin took, as protocol messages
    this.messages = history; // message data, oldest first
  }

  write(message) {
    this.actions.push(message);
  }

  async history(channelId, limit) {
    return this.messages.slice(-limit).map((data) => new Message(data, this));
  }
}

/** Dispatch one protocol event and return the actions it caused */
export async function runEvent(plugin, event, { history = [] } = {}) {
  plugin.connection = new FakeConnection(history);
  await plugin.dispatch(event);
  return plugin.connection.actions;
}

/** Run a Command like the Bot would, returning the text it sent (sends and replies) */
export async function runCommand(plugin, name, args = [], { history = [], author, channelId = '10' } = {}) {
  author ??= fakeAuthor();
  const event = {
    type: 'command',
    name,
    args,
    channel_id: channelId,
    author,
    message: fakeMessage(['!' + name, ...args].join(' '), { author, channelId }),
  };
  const actions = await runEvent(plugin, event, { history });
  return actions.filter((action) => action.type === 'send').map((action) => action.content);
}
