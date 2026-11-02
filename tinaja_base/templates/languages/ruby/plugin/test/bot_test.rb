# frozen_string_literal: true

require 'minitest/autorun'
require 'tinaja/testing'
require_relative '../bot'

class BotTest < Minitest::Test
  include Tinaja::Testing

  def test_hello_answers_world
    assert_equal ['World'], run_command(PLUGIN, 'hello')
  end

  def test_mention_answers_world
    actions = run_event(PLUGIN, { 'type' => 'mention', 'message' => fake_message('<@42> hi', id: '5'), 'text' => 'hi' })
    assert_equal [{ 'type' => 'send', 'channel_id' => '10', 'content' => 'World', 'reply_to' => '5' }], actions
  end
end
