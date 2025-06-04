import re
from typing import Optional, Tuple

from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup,
    InlineKeyboardButton, CallbackQuery
)

# Bot configuration
API_ID = 21705536  # Replace with your API ID
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"  # Replace with your API hash
BOT_TOKEN = "your_bot_token"  # Replace with your bot token

# Initialize the Pyrogram client
app = Client("channel_forwarder_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# States for conversation handling
class State:
    WAITING_FOR_SOURCE_CHANNEL = 1
    WAITING_FOR_DESTINATION_CHANNEL = 2
    WAITING_FOR_START_LINK = 3
    WAITING_FOR_END_LINK = 4
    WAITING_FOR_COUNT = 5

# User session data storage
user_sessions = {}

# Helper functions
def extract_message_info(link: str) -> Optional[Tuple[int, int]]:
    """
    Extract channel ID and message ID from a Telegram message link.
    Supports both private and public channel links.
    
    Args:
        link: The Telegram message link
        
    Returns:
        Tuple of (channel_id, message_id) or None if invalid
    """
    # Pattern for public channel links: https://t.me/channelname/123
    public_pattern = r"https?://t\.me/(?:c/)?([^/]+)/(\d+)"
    
    # Pattern for private channel links: https://t.me/c/1234567890/123
    private_pattern = r"https?://t\.me/c/(\d+)/(\d+)"
    
    # Try public pattern first
    match = re.match(public_pattern, link)
    if match:
        try:
            channel_username = match.group(1)
            message_id = int(match.group(2))
            return channel_username, message_id
        except (IndexError, ValueError):
            pass
    
    # Try private pattern
    match = re.match(private_pattern, link)
    if match:
        try:
            channel_id = int(match.group(1))
            message_id = int(match.group(2))
            return channel_id, message_id
        except (IndexError, ValueError):
            pass
    
    return None

async def get_channel_id_from_username(username: str) -> Optional[int]:
    """
    Get channel ID from username by trying to join the channel.
    
    Args:
        username: Channel username (without @)
        
    Returns:
        Channel ID or None if not found
    """
    try:
        chat = await app.get_chat(username)
        return chat.id
    except Exception:
        return None

async def verify_admin_in_channel(client: Client, channel_id: int) -> bool:
    """
    Verify if the bot is admin in the specified channel.
    
    Args:
        channel_id: The channel ID to check
        
    Returns:
        True if admin, False otherwise
    """
    try:
        chat_member = await client.get_chat_member(channel_id, "me")
        return chat_member.status in ("administrator", "creator")
    except Exception:
        return False

async def forward_message(client: Client, source_channel: int, dest_channel: int, message_id: int) -> bool:
    """
    Forward a single message from source to destination channel.
    
    Args:
        source_channel: Source channel ID
        dest_channel: Destination channel ID
        message_id: Message ID to forward
        
    Returns:
        True if successful, False otherwise
    """
    try:
        await client.forward_messages(dest_channel, source_channel, message_id)
        return True
    except Exception as e:
        print(f"Error forwarding message: {e}")
        return False

# Command handlers
@app.on_message(filters.command(["start", "help"]))
async def start_command(client: Client, message: Message):
    """Handler for /start and /help commands"""
    await message.reply_text(
        "📚 **Channel Forwarder Bot**\n\n"
        "This bot helps forward messages between channels where it's an admin.\n\n"
        "**Available Commands:**\n"
        "/forward - Start forwarding messages\n"
        "/cancel - Cancel current operation\n\n"
        "Select an option below to begin:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("All Messages", callback_data="mode_all")],
            [InlineKeyboardButton("By Start & End Links", callback_data="mode_range")],
            [InlineKeyboardButton("By Start Link & Count", callback_data="mode_count")]
        ])
    )

@app.on_message(filters.command("cancel"))
async def cancel_command(client: Client, message: Message):
    """Handler for /cancel command"""
    user_id = message.from_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await message.reply_text("❌ Operation cancelled. Any pending actions have been cleared.")

@app.on_message(filters.command("forward"))
async def forward_command(client: Client, message: Message):
    """Handler for /forward command"""
    await start_command(client, message)

# Callback query handlers
@app.on_callback_query(filters.regex("^mode_"))
async def mode_selection(client: Client, callback_query: CallbackQuery):
    """Handler for mode selection (all, range, count)"""
    user_id = callback_query.from_user.id
    mode = callback_query.data.split("_")[1]
    
    # Initialize user session
    user_sessions[user_id] = {
        "mode": mode,
        "state": State.WAITING_FOR_SOURCE_CHANNEL
    }
    
    await callback_query.message.edit_text(
        "Please send me the **source channel** (where to forward from):\n\n"
        "You can send:\n"
        "- Channel username (e.g., @channelname)\n"
        "- Channel ID (for private channels)\n"
        "- A message link from the channel"
    )
    await callback_query.answer()

# Message handlers for conversation flow
@app.on_message(filters.private & ~filters.command(["start", "help", "cancel", "forward"]))
async def handle_conversation(client: Client, message: Message):
    """Handle the conversation flow based on user's current state"""
    user_id = message.from_user.id
    
    # Check if user has an active session
    if user_id not in user_sessions:
        await message.reply_text("Please use /forward to start a new forwarding operation.")
        return
    
    session = user_sessions[user_id]
    mode = session["mode"]
    text = message.text
    
    # Step 1: Get source channel
    if session["state"] == State.WAITING_FOR_SOURCE_CHANNEL:
        # Try to extract channel info from message
        channel_info = None
        
        # Check if it's a message link
        if text.startswith("http"):
            channel_info = extract_message_info(text)
            if channel_info:
                channel_id_or_username, _ = channel_info
                if isinstance(channel_id_or_username, int):
                    channel_id = channel_id_or_username
                else:
                    channel_id = await get_channel_id_from_username(channel_id_or_username)
            else:
                await message.reply_text("❌ Invalid message link format. Please try again.")
                return
        else:
            # Check if it's a username or ID
            if text.startswith("@"):
                channel_id = await get_channel_id_from_username(text[1:])
            else:
                try:
                    channel_id = int(text)
                except ValueError:
                    await message.reply_text("❌ Invalid channel identifier. Please send a username, ID, or message link.")
                    return
        
        if not channel_id:
            await message.reply_text("❌ Channel not found. Make sure the bot has access to the channel.")
            return
        
        # Verify bot is admin in source channel
        if not await verify_admin_in_channel(client, channel_id):
            await message.reply_text("❌ Bot is not an admin in the source channel. Please make the bot admin and try again.")
            return
        
        # Store source channel and move to next state
        session["source_channel"] = channel_id
        session["state"] = State.WAITING_FOR_DESTINATION_CHANNEL
        
        await message.reply_text(
            "✅ Source channel set.\n\n"
            "Now please send me the **destination channel** (where to forward to):\n\n"
            "You can send:\n"
            "- Channel username (e.g., @channelname)\n"
            "- Channel ID (for private channels)"
        )
    
    # Step 2: Get destination channel
    elif session["state"] == State.WAITING_FOR_DESTINATION_CHANNEL:
        channel_id = None
        
        # Check if it's a username or ID
        if text.startswith("@"):
            channel_id = await get_channel_id_from_username(text[1:])
        else:
            try:
                channel_id = int(text)
            except ValueError:
                await message.reply_text("❌ Invalid channel identifier. Please send a username or ID.")
                return
        
        if not channel_id:
            await message.reply_text("❌ Channel not found. Make sure the bot has access to the channel.")
            return
        
        # Verify bot is admin in destination channel
        if not await verify_admin_in_channel(client, channel_id):
            await message.reply_text("❌ Bot is not an admin in the destination channel. Please make the bot admin and try again.")
            return
        
        # Store destination channel and proceed based on mode
        session["dest_channel"] = channel_id
        
        if mode == "all":
            # Start forwarding all messages
            await message.reply_text("🔍 Finding all messages in the source channel...")
            
            try:
                count = 0
                async for msg in client.iter_history(session["source_channel"]):
                    if await forward_message(client, session["source_channel"], session["dest_channel"], msg.message_id):
                        count += 1
                
                await message.reply_text(f"✅ Successfully forwarded {count} messages!")
            except Exception as e:
                await message.reply_text(f"❌ Error during forwarding: {e}")
            
            # Clear session
            del user_sessions[user_id]
        
        elif mode == "range":
            session["state"] = State.WAITING_FOR_START_LINK
            await message.reply_text("Please send the **start message link** (the first message to forward):")
        
        elif mode == "count":
            session["state"] = State.WAITING_FOR_START_LINK
            await message.reply_text("Please send the **start message link** (the first message to forward):")
    
    # Step 3 for range/count modes: Get start message link
    elif session["state"] == State.WAITING_FOR_START_LINK:
        if not text.startswith("http"):
            await message.reply_text("❌ Please send a valid message link starting with http:// or https://")
            return
        
        channel_info = extract_message_info(text)
        if not channel_info:
            await message.reply_text("❌ Invalid message link format. Please try again.")
            return
        
        channel_id_or_username, message_id = channel_info
        
        # Verify the message is from the source channel
        if isinstance(channel_id_or_username, str):
            # It's a username, need to get channel ID
            actual_channel_id = await get_channel_id_from_username(channel_id_or_username)
            if actual_channel_id != session["source_channel"]:
                await message.reply_text("❌ The message link must be from the source channel you specified earlier.")
                return
        else:
            # It's a channel ID
            if channel_id_or_username != session["source_channel"]:
                await message.reply_text("❌ The message link must be from the source channel you specified earlier.")
                return
        
        # Store start message ID
        session["start_message_id"] = message_id
        
        if mode == "range":
            session["state"] = State.WAITING_FOR_END_LINK
            await message.reply_text("Please send the **end message link** (the last message to forward):")
        elif mode == "count":
            session["state"] = State.WAITING_FOR_COUNT
            await message.reply_text("Please send the **number of messages** to forward (including the start message):")
    
    # Step 4 for range mode: Get end message link
    elif session["state"] == State.WAITING_FOR_END_LINK:
        if not text.startswith("http"):
            await message.reply_text("❌ Please send a valid message link starting with http:// or https://")
            return
        
        channel_info = extract_message_info(text)
        if not channel_info:
            await message.reply_text("❌ Invalid message link format. Please try again.")
            return
        
        channel_id_or_username, message_id = channel_info
        
        # Verify the message is from the source channel
        if isinstance(channel_id_or_username, str):
            # It's a username, need to get channel ID
            actual_channel_id = await get_channel_id_from_username(channel_id_or_username)
            if actual_channel_id != session["source_channel"]:
                await message.reply_text("❌ The message link must be from the source channel you specified earlier.")
                return
        else:
            # It's a channel ID
            if channel_id_or_username != session["source_channel"]:
                await message.reply_text("❌ The message link must be from the source channel you specified earlier.")
                return
        
        # Store end message ID
        session["end_message_id"] = message_id
        
        # Start forwarding the range
        await message.reply_text("⏳ Forwarding messages in the specified range...")
        
        try:
            start_id = min(session["start_message_id"], session["end_message_id"])
            end_id = max(session["start_message_id"], session["end_message_id"])
            count = 0
            
            for msg_id in range(start_id, end_id + 1):
                if await forward_message(client, session["source_channel"], session["dest_channel"], msg_id):
                    count += 1
            
            await message.reply_text(f"✅ Successfully forwarded {count} messages!")
        except Exception as e:
            await message.reply_text(f"❌ Error during forwarding: {e}")
        
        # Clear session
        del user_sessions[user_id]
    
    # Step 4 for count mode: Get message count
    elif session["state"] == State.WAITING_FOR_COUNT:
        try:
            count = int(text)
            if count <= 0:
                await message.reply_text("❌ Please enter a positive number.")
                return
        except ValueError:
            await message.reply_text("❌ Please enter a valid number.")
            return
        
        # Start forwarding the count
        await message.reply_text(f"⏳ Forwarding {count} messages starting from the specified message...")
        
        try:
            start_id = session["start_message_id"]
            forwarded = 0
            
            for msg_id in range(start_id, start_id + count):
                if await forward_message(client, session["source_channel"], session["dest_channel"], msg_id):
                    forwarded += 1
                else:
                    # Stop if we can't forward a message (might have reached the end)
                    break
            
            await message.reply_text(f"✅ Successfully forwarded {forwarded} messages!")
        except Exception as e:
            await message.reply_text(f"❌ Error during forwarding: {e}")
        
        # Clear session
        del user_sessions[user_id]

# Error handler
@app.on_message(filters.private)
async def error_handler(client: Client, message: Message):
    """Handle unexpected messages"""
    await message.reply_text(
        "I didn't understand that. Please use /forward to start a new forwarding operation "
        "or /cancel to cancel the current one."
    )

# Start the bot
if __name__ == "__main__":
    print("Bot started...")
    app.run()
