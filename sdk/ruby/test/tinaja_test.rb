# frozen_string_literal: true

require 'minitest/autorun'
require 'stringio'
require 'tinaja/testing'

class TinajaTest < Minitest::Test
  include Tinaja::Testing

  def setup
    @plugin = Tinaja::Plugin.new
    @plugin.command('hello', help: 'Says World') { |ctx| ctx.send("World, #{ctx.author.display_name}") }
    @plugin.command('last') { |ctx| ctx.reply(ctx.history(1).first.content) }
    @plugin.on_message { |message| message.react('🏓') }
  end

  def test_run_command_returns_what_was_sent
    assert_equal ['World, jane'], run_command(@plugin, 'hello', author: fake_author('jane'))
  end

  def test_history_comes_from_the_given_messages
    assert_equal ['new'], run_command(@plugin, 'last', history: [fake_message('old'), fake_message('new')])
  end

  def test_run_event_returns_actions
    actions = run_event(@plugin, { 'type' => 'message', 'message' => fake_message('ping', id: '7') })
    assert_equal [{ 'type' => 'react', 'channel_id' => '10', 'message_id' => '7', 'emoji' => '🏓' }], actions
  end

  def test_registration_lists_commands_and_events
    assert_equal(
      { 'type' => 'register', 'commands' => [{ 'name' => 'hello', 'help' => 'Says World' }, { 'name' => 'last', 'help' => '' }],
        'events' => ['message'] },
      @plugin.registration
    )
  end

  def test_a_failing_handler_does_not_stop_the_plugin
    @plugin.command('boom') { raise 'boom' }
    input = StringIO.new(<<~JSONL)
      {"type": "hello", "protocol": 1, "bot": {}}
      {"type": "command", "name": "boom", "args": [], "channel_id": "10"}
      {"type": "command", "name": "hello", "args": [], "channel_id": "10", "author": {"name": "jane"}}
    JSONL
    output = StringIO.new
    _, stderr = capture_io { @plugin.run(input, output) }
    lines = output.string.lines.map { |line| JSON.parse(line) }
    assert_equal %w[register send], lines.map { |line| line['type'] }
    assert_equal 'World, jane', lines.last['content']
    assert_includes stderr, 'boom'
  end
end
