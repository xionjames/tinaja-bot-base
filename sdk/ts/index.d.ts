export declare const PROTOCOL: 1;

export interface Author {
  id: string;
  name: string;
  displayName: string;
  mention: string;
  bot: boolean;
}

/** A protocol message as JSON: ids are strings, keys are snake_case */
export interface MessageData {
  id: string;
  content: string;
  channel_id: string;
  author: { id: string; name: string; display_name?: string; mention?: string; bot?: boolean };
}

export type Event = { type: string; [key: string]: unknown };
export type Action = { type: string; [key: string]: unknown };

/** Anything the SDK can write actions to and request history from */
export interface Writer {
  write(message: Action): void;
  history(channelId: string, limit: number): Promise<Message[]>;
}

export declare class Message {
  constructor(data: Partial<MessageData> | undefined, connection: Writer);
  readonly id: string;
  readonly content: string;
  readonly channelId: string;
  readonly author: Author;
  reply(content: string): void;
  react(emoji: string): void;
}

/** What a Command handler gets: who asked, where, and the words after the Command */
export declare class Context {
  readonly name: string;
  readonly args: string[];
  readonly channelId: string;
  readonly author: Author;
  readonly message: Message;
  send(content: string): void;
  reply(content: string): void;
  /** The channel's latest Member messages, oldest first */
  history(limit?: number): Promise<Message[]>;
}

export declare class Connection implements Writer {
  constructor(input: NodeJS.ReadableStream, output: NodeJS.WritableStream);
  write(message: Action): void;
  read(): Promise<Event | null>;
  history(channelId: string, limit: number): Promise<Message[]>;
  close(): void;
}

type Awaitable = void | Promise<void>;

export declare class Plugin {
  connection: Writer | null;
  /** The hello's bot info: name, prefix, id */
  bot: { name?: string; prefix?: string; id?: string | null };
  command(name: string, handler: (ctx: Context) => Awaitable): this;
  command(name: string, options: { help?: string }, handler: (ctx: Context) => Awaitable): this;
  onMessage(handler: (message: Message) => Awaitable): this;
  /** Needs a [mentions] table in bot.toml */
  onMention(handler: (message: Message, text: string) => Awaitable): this;
  send(channelId: string, content: string): void;
  history(channelId: string, limit?: number): Promise<Message[]>;
  registration(): { type: 'register'; commands: { name: string; help: string }[]; events: string[] };
  /** Serve the host until it says shutdown or closes stdin */
  run(input?: NodeJS.ReadableStream, output?: NodeJS.WritableStream): Promise<void>;
  handle(event: Event): Promise<void>;
  /** Handle one event, letting handler errors through */
  dispatch(event: Event): Promise<void>;
}
