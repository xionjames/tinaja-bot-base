# frozen_string_literal: true

require 'tinaja'

# Ruby Bot's Commands and listeners. Log with warn (stderr): stdout is reserved for the protocol.
PLUGIN = Tinaja::Plugin.new

PLUGIN.command('hello', help: 'Says World') { |ctx| ctx.send('World') }

PLUGIN.command('recap', help: 'The latest messages in the channel: !recap [n]') do |ctx|
  count = (ctx.args.first || 5).to_i.clamp(1, 20)
  # +1 because the !recap message itself is the newest one in the channel
  messages = ctx.history(count + 1).reject { |m| m.id == ctx.message.id }.last(count)
  ctx.send(messages.empty? ? 'Nothing to recap yet.' : messages.map { |m| "#{m.author.display_name}: #{m.content}" }.join("\n"))
end

# The plugin is one long-running process, so plain variables keep state between messages
SEEN = Hash.new(0)

PLUGIN.on_message { |message| SEEN[message.author.display_name] += 1 }

PLUGIN.command('seen', help: 'How many messages each Member wrote since the bot started') do |ctx|
  ctx.send(SEEN.empty? ? 'Nobody wrote anything yet.' : SEEN.map { |name, count| "#{name}: #{count}" }.join("\n"))
end

PLUGIN.on_mention { |message, _text| message.reply('World') }

PLUGIN.run if $PROGRAM_NAME == __FILE__
