# frozen_string_literal: true

require 'minitest/autorun'
require 'tinaja/testing'
require_relative '../bot'

class BotTest < Minitest::Test
  include Tinaja::Testing

  def setup
    SEEN.clear
  end

  def test_hello_answers_world
    assert_equal ['World'], run_command(PLUGIN, 'hello')
  end

  def test_recap_leaves_out_the_recap_message_itself
    history = [fake_message('hi all', author: fake_author('bob'), id: '1'), fake_message('!recap 1', id: '100')]
    assert_equal ['bob: hi all'], run_command(PLUGIN, 'recap', '1', history: history)
  end

  def test_recap_without_messages
    assert_equal ['Nothing to recap yet.'], run_command(PLUGIN, 'recap')
  end

  def test_seen_counts_messages
    2.times { run_event(PLUGIN, { 'type' => 'message', 'message' => fake_message('hola', author: fake_author('ana')) }) }
    assert_equal ['ana: 2'], run_command(PLUGIN, 'seen')
  end

  def test_mention_answers_world
    actions = run_event(PLUGIN, { 'type' => 'mention', 'message' => fake_message('<@42> hi', id: '5'), 'text' => 'hi' })
    assert_equal [{ 'type' => 'send', 'channel_id' => '10', 'content' => 'World', 'reply_to' => '5' }], actions
  end
end
