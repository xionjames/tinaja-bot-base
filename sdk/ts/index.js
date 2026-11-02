// SDK for tinaja-bot-base Plugins: a Bot's Commands and listeners written in TypeScript or JavaScript.
// The Bot (a Python host) runs this process and talks to it over stdin/stdout, see docs/protocol.md.
import { createInterface } from 'node:readline';

export const PROTOCOL = 1;

function author(data = {}) {
  const name = data.name ?? '';
  return {
    id: data.id,
    name,
    displayName: data.display_name ?? name,
    mention: data.mention ?? '',
    bot: data.bot ?? false,
  };
}

export class Message {
  constructor(data = {}, connection) {
    this.id = data.id;
    this.content = data.content ?? '';
    this.channelId = data.channel_id;
    this.author = author(data.author);
    this.connection = connection;
  }

  reply(content) {
    this.connection.write({ type: 'send', channel_id: this.channelId, content: String(content), reply_to: this.id });
  }

  react(emoji) {
    this.connection.write({ type: 'react', channel_id: this.channelId, message_id: this.id, emoji });
  }
}

/** What a Command handler gets: who asked, where, and the words after the Command */
export class Context {
  constructor(event, connection) {
    this.name = event.name;
    this.args = event.args ?? [];
    this.channelId = event.channel_id;
    this.author = author(event.author);
    this.message = new Message(event.message, connection);
    this.connection = connection;
  }

  send(content) {
    this.connection.write({ type: 'send', channel_id: this.channelId, content: String(content) });
  }

  reply(content) {
    this.message.reply(content);
  }

  /** The channel's latest Member messages, oldest first */
  history(limit = 20) {
    return this.connection.history(this.channelId, limit);
  }
}

/** JSON lines over a pair of streams */
export class Connection {
  constructor(input, output) {
    this.output = output;
    this.queue = []; // events waiting to be handled
    this.reader = null; // resolves read() when the queue is empty
    this.requests = new Map(); // request_id -> {resolve, reject}
    // Answers that arrive before history() registers its request: stdin can be read ahead of the handlers
    this.answers = new Map();
    this.nextId = 1;
    this.closed = false;
    this.lines = createInterface({ input, crlfDelay: Infinity });
    this.lines.on('line', (line) => line.trim() && this.receive(JSON.parse(line)));
    this.lines.on('close', () => this.close());
  }

  write(message) {
    this.output.write(JSON.stringify(message) + '\n');
  }

  /** The next event, or null when the host closed stdin */
  read() {
    if (this.queue.length) return Promise.resolve(this.queue.shift());
    if (this.closed) return Promise.resolve(null);
    return new Promise((resolve) => (this.reader = resolve));
  }

  history(channelId, limit) {
    const requestId = String(this.nextId++);
    return new Promise((resolve, reject) => {
      this.requests.set(requestId, { resolve, reject });
      this.write({ type: 'history', request_id: requestId, channel_id: channelId, limit });
      if (this.answers.has(requestId)) this.answer(this.answers.get(requestId));
      else if (this.closed) this.answer({ type: 'error', request_id: requestId, error: 'the host closed the connection' });
    }).then((event) => (event.messages ?? []).map((data) => new Message(data, this)));
  }

  receive(event) {
    if ((event.type === 'result' || event.type === 'error') && event.request_id !== undefined) {
      if (this.requests.has(event.request_id)) this.answer(event);
      else this.answers.set(event.request_id, event);
      return;
    }
    // Events that arrive while a handler awaits a result are handled after it, in order
    if (this.reader) {
      const reader = this.reader;
      this.reader = null;
      reader(event);
    } else {
      this.queue.push(event);
    }
  }

  answer(event) {
    const request = this.requests.get(event.request_id);
    this.requests.delete(event.request_id);
    this.answers.delete(event.request_id);
    if (event.type === 'error') request.reject(new Error(event.error ?? 'history failed'));
    else request.resolve(event);
  }

  close() {
    if (this.closed) return;
    this.closed = true;
    this.lines.close();
    for (const { reject } of this.requests.values()) reject(new Error('the host closed the connection'));
    this.requests.clear();
    if (this.reader) this.reader(null);
  }
}

export class Plugin {
  constructor() {
    this.commands = new Map(); // name -> {help, handler}, in registration order
    this.messageHandlers = [];
    this.mentionHandlers = [];
    this.connection = null;
    this.bot = {}; // the hello's bot info: name, prefix, id
  }

  /** command(name, handler) or command(name, {help}, handler): handler(ctx) runs for every !name */
  command(name, options, handler) {
    if (typeof options === 'function') [options, handler] = [{}, options];
    this.commands.set(name, { help: options?.help ?? '', handler });
    return this;
  }

  /** handler(message) runs for every message from a Member, Commands included */
  onMessage(handler) {
    this.messageHandlers.push(handler);
    return this;
  }

  /** handler(message, text) runs when the Bot is @mentioned without a Command; needs [mentions] in bot.toml */
  onMention(handler) {
    this.mentionHandlers.push(handler);
    return this;
  }

  send(channelId, content) {
    this.connection.write({ type: 'send', channel_id: channelId, content: String(content) });
  }

  history(channelId, limit = 20) {
    return this.connection.history(channelId, limit);
  }

  registration() {
    const events = { message: this.messageHandlers, mention: this.mentionHandlers };
    return {
      type: 'register',
      commands: [...this.commands].map(([name, { help }]) => ({ name, help })),
      events: Object.keys(events).filter((name) => events[name].length).sort(),
    };
  }

  /** Serve the host until it says shutdown or closes stdin */
  async run(input = process.stdin, output = process.stdout) {
    this.connection = new Connection(input, output);
    let event;
    while ((event = await this.connection.read()) !== null) {
      if (event.type === 'shutdown') break;
      await this.handle(event);
    }
    this.connection.close();
  }

  async handle(event) {
    try {
      await this.dispatch(event);
    } catch (error) {
      // one failing handler mustn't stop the Plugin
      console.error(error);
    }
  }

  /** Handle one event, letting handler errors through (handle() logs them instead) */
  async dispatch(event) {
    switch (event.type) {
      case 'hello':
        this.bot = event.bot ?? {};
        this.connection.write(this.registration());
        break;
      case 'command': {
        const command = this.commands.get(event.name);
        if (command) await command.handler(new Context(event, this.connection));
        break;
      }
      case 'message':
        for (const handler of this.messageHandlers) await handler(new Message(event.message, this.connection));
        break;
      case 'mention':
        for (const handler of this.mentionHandlers) {
          await handler(new Message(event.message, this.connection), event.text ?? '');
        }
        break;
      case 'error':
        console.error(`tinaja: the host reported an error: ${event.error}`);
        break;
      // anything else (ready, future events) needs no answer
    }
  }
}
