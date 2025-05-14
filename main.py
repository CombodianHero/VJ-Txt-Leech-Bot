from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import os

# --- Configuration ---
API_ID = 21705536  # Replace with your actual API ID
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"  # Replace with your actual API HASH
BOT_TOKEN = "7740653447:AAFbJ_iAr__2LgYO0TZIDkle81CUsayj4us"  # Replace with your actual bot token
CHANNEL_USERNAME = "Engineersbabuupdates"  # Without @

# --- MongoDB Setup ---
mongo = MongoClient("mongodb+srv://engineersbabuxtract:ETxVh71rTNDpmHaj@cluster0.kofsig4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo["telegram_bot"]
verified_users = db["verified_users"]

# --- Bot Client ---
bot = Client("force_join_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Check if User Joined Channel ---
async def is_user_joined(client: Client, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        return False

# --- /start Command ---
@bot.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    user_id = message.from_user.id

    if await is_user_joined(client, user_id):
        # Store in MongoDB if not already stored
        if not verified_users.find_one({"user_id": user_id}):
            verified_users.insert_one({
                "user_id": user_id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "verified": True
            })
        await message.reply_text(
            "✅ You are verified!\n\n"
            "Now send me a `.txt` file to extract and read its content."
        )
    else:
        await message.reply_text(
            f"❌ You must join our channel first to use this bot.\n\n"
            f"➡️ [Join Channel](https://t.me/{CHANNEL_USERNAME})\n"
            "Then press /start again.",
            disable_web_page_preview=True
        )

# --- Handle .txt Files ---
@bot.on_message(filters.document & filters.private)
async def handle_txt_file(client: Client, message: Message):
    user_id = message.from_user.id

    # Verify from MongoDB
    if not verified_users.find_one({"user_id": user_id}):
        await message.reply_text("❌ You are not verified yet. Join the channel and send /start.")
        return

    doc = message.document
    if doc.mime_type != "text/plain":
        await message.reply_text("❗ Please send a `.txt` file only.")
        return

    # Download and Read File
    file_path = await client.download_media(doc)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        await message.reply_text(f"📝 Content of your file:\n\n{content[:4000]}")
    except Exception as e:
        await message.reply_text("⚠️ Failed to read the file.")
    finally:
        os.remove(file_path)

# --- Run the Bot ---
bot.run()
