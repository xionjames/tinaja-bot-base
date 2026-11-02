# frozen_string_literal: true

# The reference behaviour from sdk/conformance/README.md
$LOAD_PATH.unshift(File.expand_path('../lib', __dir__))
require 'tinaja'

plugin = Tinaja::Plugin.new

plugin.command('hello', help: 'Says World') { |ctx| ctx.send('World') }

plugin.command('echo', help: 'Repeats what you say') do |ctx|
  ctx.send(ctx.args.empty? ? 'Nothing to echo' : ctx.args.join(' '))
end

plugin.command('recap', help: 'The latest messages in the channel') do |ctx|
  messages = ctx.history((ctx.args.first || 5).to_i)
  lines = messages.map { |m| "#{m.author.display_name}: #{m.content}" }
  ctx.send(lines.empty? ? 'Nothing to recap yet.' : lines.join("\n"))
end

plugin.on_mention { |message, text| message.reply("You said: #{text}") }

plugin.on_message { |message| message.react('🏓') if message.content == 'ping' }

plugin.run
