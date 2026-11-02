# frozen_string_literal: true

require 'tinaja'

module Tinaja
  # Run a Plugin's handlers without a Bot: what they send is recorded, history comes from a list
  module Testing
    class FakeConnection
      attr_reader :actions # every action the Plugin took, as protocol messages

      def initialize(history = [])
        @actions = []
        @history = history # message hashes, oldest first
      end

      def write(message)
        @actions << message
      end

      def history(_channel_id, limit)
        @history.last(limit).map { |data| Message.new(data, self) }
      end
    end

    module_function

    def fake_author(name = 'member', id: '1', bot: false)
      { 'id' => id, 'name' => name, 'display_name' => name, 'mention' => "<@#{id}>", 'bot' => bot }
    end

    def fake_message(content, author: nil, id: '100', channel_id: '10')
      { 'id' => id, 'content' => content, 'channel_id' => channel_id, 'author' => author || fake_author }
    end

    # Dispatch one protocol event and return the actions it caused
    def run_event(plugin, event, history: [])
      plugin.connection = FakeConnection.new(history)
      plugin.dispatch(event)
      plugin.connection.actions
    end

    # Run a Command like the Bot would, returning the text it sent (sends and replies)
    def run_command(plugin, name, *args, history: [], author: nil, channel_id: '10')
      author ||= fake_author
      event = {
        'type' => 'command', 'name' => name, 'args' => args, 'channel_id' => channel_id, 'author' => author,
        'message' => fake_message(['!' + name, *args].join(' '), author: author, channel_id: channel_id)
      }
      run_event(plugin, event, history: history).select { |a| a['type'] == 'send' }.map { |a| a['content'] }
    end
  end
end
