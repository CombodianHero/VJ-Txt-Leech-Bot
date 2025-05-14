from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant
import os

# Bot credentials
API_ID = 21705536
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7740653447:AAFbJ_iAr__2LgYO0TZIDkle81CUsayj4us"
FORCE_CHANNEL = "@engineersbabu"

# Initialize the bot client
app = Client("force_join_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# Function to check if a user has joined the force channel
async def is_user_joined(user_id: int) -> bool:
    try:
        member = await app.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"[ERROR] Checking membership failed: {e}")
        return False


# /start command handler
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    user = message.from_user

    if not await is_user_joined(user.id):
        join_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNEL.strip('@')}")],
            [InlineKeyboardButton("✅ I Have Joined", callback_data="recheck_join")]
        ])

        await message.reply_text(
            f"👋 Hello {user.first_name},\n\n🔒 You need to **join our channel** to use this bot.",
            reply_markup=join_button
        )
        return

    await message.reply_text("✅ You're verified!\nNow send me a `.txt` file to process.")


# Callback query to recheck if user has joined
@app.on_callback_query(filters.regex("recheck_join"))
async def recheck_join(client, callback_query):
    user_id = callback_query.from_user.id

    if await is_user_joined(user_id):
        await callback_query.message.edit("🎉 You've joined the channel!\nNow send me a `.txt` file.")
    else:
        await callback_query.answer("❌ You're still not a member of the channel.", show_alert=True)


# Handler for receiving .txt files
@app.on_message(filters.private & filters.document)
async def handle_txt_file(client, message: Message):
    user_id = message.from_user.id

    if not await is_user_joined(user_id):
        await message.reply_text("❌ You must join the channel first to use this feature.")
        return

    document = message.document

    if not document.file_name.endswith(".txt"):
        await message.reply_text("⚠️ Please send a valid `.txt` file.")
        return

    file_path = await document.download()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Telegram message limit is 4096 characters
        await message.reply_text(f"📝 File Content:\n\n{content[:4096]}")
    except Exception as e:
        await message.reply_text(f"❌ Failed to read the file: {e}")
    finally:
        os.remove(file_path)


# Run the bot
app.run()
