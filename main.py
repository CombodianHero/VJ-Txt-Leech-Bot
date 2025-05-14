from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant
import os

# Bot credentials
API_ID = 21705536
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7740653447:AAFbJ_iAr__2LgYO0TZIDkle81CUsayj4us"
FORCE_CHANNEL = "@Engineersbabuupdates"

# Create the client
app = Client("ForceJoinBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# Function to check membership
async def is_user_joined(user_id: int) -> bool:
    try:
        member = await app.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ("member", "administrator", "creator")
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"Error checking user: {e}")
        return False


# Start command
@app.on_message(filters.command("start") & filters.private)
async def start(client, message: Message):
    user = message.from_user

    if not await is_user_joined(user.id):
        await message.reply(
            f"👋 Hello {user.first_name},\n\n🔒 To use this bot, you must first **join our channel**:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNEL.strip('@')}")],
                    [InlineKeyboardButton("✅ I've Joined", callback_data="check_joined")]
                ]
            )
        )
        return

    await message.reply("✅ You are verified! Now send me a `.txt` file to extract content.")


# Recheck button callback
@app.on_callback_query(filters.regex("check_joined"))
async def recheck_membership(client, callback_query):
    user_id = callback_query.from_user.id

    if await is_user_joined(user_id):
        await callback_query.message.edit("🎉 You have successfully joined the channel!\nNow send me a `.txt` file.")
    else:
        await callback_query.answer("❌ You haven't joined the channel yet!", show_alert=True)


# Handle .txt files
@app.on_message(filters.document & filters.private)
async def handle_txt(client, message: Message):
    user_id = message.from_user.id

    if not await is_user_joined(user_id):
        await message.reply("❌ You must join the channel first to use the bot.")
        return

    doc = message.document
    if not doc.file_name.endswith(".txt"):
        await message.reply("⚠️ Please send a valid `.txt` file.")
        return

    file_path = await doc.download()
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Reply with content (limited to first 4096 chars)
    await message.reply(f"📝 File Content:\n\n{content[:4096]}")
    os.remove(file_path)


# Run the bot
app.run()
