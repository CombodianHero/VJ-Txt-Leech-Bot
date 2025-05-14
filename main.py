from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import UserNotParticipant

API_ID = "21705536"
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7740653447:AAFbJ_iAr__2LgYO0TZIDkle81CUsayj4us"
CHANNEL_USERNAME = "Engineersbabuupdates"  # without @

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Helper: Check if user is in the channel
async def is_user_in_channel(user_id):
    try:
        member = await app.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except UserNotParticipant:
        return False
    except Exception:
        return False

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    user_id = message.from_user.id
    if not await is_user_in_channel(user_id):
        await message.reply(
            f"🚫 To use this bot, please join our channel first:\n"
            f"https://t.me/{CHANNEL_USERNAME}\n\n"
            "After joining, press /start again."
        )
        return
    await message.reply("✅ Welcome! Send a user ID to get their current profile info.")

@app.on_message(filters.private & filters.regex(r"^\d+$"))
async def get_user_info(client, message: Message):
    user_id = int(message.text)
    try:
        user = await app.get_users(user_id)
        info = (
            f"👤 Name: {user.first_name or ''} {user.last_name or ''}\n"
            f"🔗 Username: @{user.username if user.username else 'None'}\n"
            f"🆔 User ID: {user.id}\n"
            f"🌐 Language: {user.language_code if hasattr(user, 'language_code') else 'Unknown'}\n"
            f"🤖 Is Bot: {user.is_bot}\n"
        )
        await message.reply(info)
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

app.run()
