# tinaja (Ruby SDK)
Write the Commands and listeners of a [tinaja-bot-base](../..) Bot in Ruby. Plain Ruby, only `json` from the standard
library. `tinaja-bot new "My Bot" --lang ruby` sets everything up; to add it by hand:
```ruby
# Gemfile
gem 'tinaja', git: 'https://github.com/xionjames/tinaja-bot-base', ref: 'main', glob: 'sdk/ruby/*.gemspec'
```
```ruby
require 'tinaja'

plugin = Tinaja::Plugin.new
plugin.command('hello', help: 'Says World') { |ctx| ctx.send('World') }     # ctx.args, ctx.author, ctx.reply
plugin.command('recap') { |ctx| ctx.send(ctx.history(5).map(&:content).join("\n")) }
plugin.on_message { |message| message.react('👀') if message.content.include?('bot') }
plugin.on_mention { |message, text| message.reply("You said: #{text}") }
plugin.run
```
- `Context`: `name`, `args`, `channel_id`, `author`, `message`, `send(text)`, `reply(text)`, `history(limit = 20)`
- `Message`: `id`, `content`, `channel_id`, `author`, `reply(text)`, `react(emoji)`
- `Author`: `id`, `name`, `display_name`, `mention`, `bot`
- `plugin.send(channel_id, text)` and `plugin.history(channel_id, limit)` work outside handlers too.

Handlers run one at a time. An exception in a handler is logged to stderr and the Plugin keeps running.

## Testing
```ruby
require 'tinaja/testing'
include Tinaja::Testing

run_command(plugin, 'hello')                                       # => ["World"]
run_command(plugin, 'recap', history: [fake_message('hi')])        # history comes from the list
run_event(plugin, { 'type' => 'message', 'message' => fake_message('bot?') })   # => the actions, as protocol hashes
```

## Develop
```bash
bundle install && bundle exec rake test
uv run python ../conformance/run.py -- ruby conformance/plugin.rb
```
