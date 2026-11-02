# frozen_string_literal: true

Gem::Specification.new do |spec|
  spec.name = 'tinaja'
  spec.version = '0.1.0'
  spec.summary = 'Write tinaja-bot-base Plugins (Discord Bot Commands and listeners) in Ruby'
  spec.authors = ['tinaja-bot-base']
  spec.license = 'MIT'
  spec.homepage = 'https://github.com/xionjames/tinaja-bot-base'
  spec.required_ruby_version = '>= 3.2'
  spec.files = Dir['lib/**/*.rb']
  spec.require_paths = ['lib']
end
