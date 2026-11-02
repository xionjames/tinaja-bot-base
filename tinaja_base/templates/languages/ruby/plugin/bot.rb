# frozen_string_literal: true

require 'tinaja'

# $bot_name's Commands and listeners. The bot runs this file and talks to it over stdin/stdout,
# so log with warn (stderr): anything printed to stdout must be protocol messages.
PLUGIN = Tinaja::Plugin.new

PLUGIN.command('hello', help: 'Says World') { |ctx| ctx.send('World') }

PLUGIN.on_mention { |message, _text| message.reply('World') }

PLUGIN.run if $PROGRAM_NAME == __FILE__
