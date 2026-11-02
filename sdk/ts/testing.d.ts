import type { Action, Event, Message, MessageData, Plugin, Writer } from './index.js';

export declare function fakeAuthor(name?: string, options?: { id?: string; bot?: boolean }): MessageData['author'];
export declare function fakeMessage(
  content: string,
  options?: { author?: MessageData['author']; id?: string; channelId?: string },
): MessageData;

export declare class FakeConnection implements Writer {
  constructor(history?: MessageData[]);
  /** Every action the Plugin took, as protocol messages */
  actions: Action[];
  write(message: Action): void;
  history(channelId: string, limit: number): Promise<Message[]>;
}

/** Dispatch one protocol event and return the actions it caused */
export declare function runEvent(plugin: Plugin, event: Event, options?: { history?: MessageData[] }): Promise<Action[]>;

/** Run a Command like the Bot would, returning the text it sent (sends and replies) */
export declare function runCommand(
  plugin: Plugin,
  name: string,
  args?: string[],
  options?: { history?: MessageData[]; author?: MessageData['author']; channelId?: string },
): Promise<string[]>;
