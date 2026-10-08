async def recent_messages(channel, limit=20, include_bots=False):
    """The latest messages in a channel, oldest first; needs the message_content intent to read their text"""
    messages = [m async for m in channel.history(limit=limit) if include_bots or not m.author.bot]
    messages.reverse()
    return messages
