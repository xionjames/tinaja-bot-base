# frozen_string_literal: true

require 'json'

# SDK for tinaja-bot-base Plugins: a Bot's Commands and listeners written in Ruby.
# The Bot (a Python host) runs this process and talks to it over stdin/stdout, see docs/protocol.md.
module Tinaja
  PROTOCOL = 1

  Author = Struct.new(:id, :name, :display_name, :mention, :bot, keyword_init: true) do
    def self.from(data)
      new(id: data['id'], name: data['name'].to_s, display_name: data['display_name'] || data['name'].to_s,
          mention: data['mention'].to_s, bot: data['bot'] || false)
    end
  end

  class Message
    attr_reader :id, :content, :channel_id, :author

    def initialize(data, connection)
      @id = data['id']
      @content = data['content'].to_s
      @channel_id = data['channel_id']
      @author = Author.from(data['author'] || {})
      @connection = connection
    end

    def reply(content)
      @connection.write('type' => 'send', 'channel_id' => channel_id, 'content' => content.to_s, 'reply_to' => id)
    end

    def react(emoji)
      @connection.write('type' => 'react', 'channel_id' => channel_id, 'message_id' => id, 'emoji' => emoji)
    end
  end

  # What a Command handler gets: who asked, where, and the words after the Command
  class Context
    attr_reader :name, :args, :channel_id, :author, :message

    def initialize(event, connection)
      @name = event['name']
      @args = event['args'] || []
      @channel_id = event['channel_id']
      @author = Author.from(event['author'] || {})
      @message = Message.new(event['message'] || {}, connection)
      @connection = connection
    end

    def send(content)
      @connection.write('type' => 'send', 'channel_id' => channel_id, 'content' => content.to_s)
    end

    def reply(content)
      message.reply(content)
    end

    # The channel's latest Member messages, oldest first
    def history(limit = 20)
      @connection.history(channel_id, limit)
    end
  end

  # JSON lines over a pair of IOs
  class Connection
    def initialize(reader, writer)
      @reader = reader
      @writer = writer
      @pending = [] # events that arrived while waiting for a result
      @next_id = 1
    end

    def write(message)
      @writer.puts(JSON.generate(message))
      @writer.flush
    end

    # The next event, or nil when the host closed stdin
    def read
      @pending.empty? ? read_line : @pending.shift
    end

    def history(channel_id, limit)
      request_id = @next_id.to_s
      @next_id += 1
      write('type' => 'history', 'request_id' => request_id, 'channel_id' => channel_id, 'limit' => limit)
      while (event = read_line)
        if event['request_id'] == request_id && %w[result error].include?(event['type'])
          raise Error, event['error'] || 'history failed' if event['type'] == 'error'

          return (event['messages'] || []).map { |data| Message.new(data, self) }
        end
        @pending << event
      end
      raise EOFError, 'the host closed the connection'
    end

    private

    def read_line
      while (line = @reader.gets)
        return JSON.parse(line) unless line.strip.empty?
      end
      nil
    end
  end

  class Error < StandardError; end

  class Plugin
    attr_accessor :connection
    attr_reader :bot # the hello's bot info: name, prefix, id

    def initialize
      @commands = {} # name => [help, handler], in registration order
      @message_handlers = []
      @mention_handlers = []
      @bot = {}
    end

    # The block runs with a Context for every !name
    def command(name, help: '', &handler)
      @commands[name.to_s] = [help, handler]
    end

    # The block runs with a Message for every message from a Member, Commands included
    def on_message(&handler)
      @message_handlers << handler
    end

    # The block runs with (message, text) when the Bot is @mentioned without a Command; needs [mentions] in bot.toml
    def on_mention(&handler)
      @mention_handlers << handler
    end

    def send(channel_id, content)
      connection.write('type' => 'send', 'channel_id' => channel_id, 'content' => content.to_s)
    end

    def history(channel_id, limit = 20)
      connection.history(channel_id, limit)
    end

    def registration
      events = { 'message' => @message_handlers, 'mention' => @mention_handlers }
      {
        'type' => 'register',
        'commands' => @commands.map { |name, (help, _)| { 'name' => name, 'help' => help } },
        'events' => events.reject { |_, handlers| handlers.empty? }.keys.sort
      }
    end

    # Serve the host until it says shutdown or closes stdin
    def run(reader = $stdin, writer = $stdout)
      reader.set_encoding('UTF-8') if reader.respond_to?(:set_encoding)
      @connection = Connection.new(reader, writer)
      while (event = @connection.read)
        break if event['type'] == 'shutdown'

        handle(event)
      end
    end

    def handle(event)
      dispatch(event)
    rescue StandardError => e # one failing handler mustn't stop the Plugin
      warn e.full_message
    end

    # Handle one event, letting handler errors through (handle logs them instead)
    def dispatch(event)
      case event['type']
      when 'hello'
        @bot = event['bot'] || {}
        connection.write(registration)
      when 'command'
        _, handler = @commands[event['name']]
        handler&.call(Context.new(event, connection))
      when 'message'
        @message_handlers.each { |handler| handler.call(Message.new(event['message'] || {}, connection)) }
      when 'mention'
        message = Message.new(event['message'] || {}, connection)
        @mention_handlers.each { |handler| handler.call(message, event['text'].to_s) }
      when 'error'
        warn "tinaja: the host reported an error: #{event['error']}"
      end
      # anything else (ready, future events) needs no answer
    end
  end
end
