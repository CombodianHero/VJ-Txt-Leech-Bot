import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient

# --- Configuration ---
API_ID = 21705536
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7740653447:AAFbJ_iAr__2LgYO0TZIDkle81CUsayj4us"
CHANNEL_USERNAME = "Engineersbabuupdates"  # No '@'

# --- MongoDB Setup ---
mongo = MongoClient("mongodb+srv://engineersbabuxtract:ETxVh71rTNDpmHaj@cluster0.kofsig4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo["telegram_bot"]
verified_users = db["verified_users"]

# --- Pyrogram Bot ---
bot = Client("force_join_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Check Channel Membership ---
async def is_user_joined(client: Client, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(CHANNEL_USERNAME, user_id)
        print(f"[DEBUG] user_id={user_id}, status={member.status}")
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"[ERROR] Failed to check membership for user {user_id}: {e}")
        return False

# --- /start Command ---
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user = message.from_user
    user_id = user.id

    if await is_user_joined(client, user_id):
        if not verified_users.find_one({"user_id": user_id}):
            verified_users.insert_one({
                "user_id": user_id,
                "username": user.username or None,
                "first_name": user.first_name or "",
                "verified": True
            })

        await message.reply_text(
            f"✅ Hello {user.first_name or 'User'}, you are verified!\n\n"
            "Now send me a `.txt` file to extract and read its content."
        )
    else:
        await message.reply_text(
            f"❌ You must join our channel first to use this bot.\n\n"
            f"👉 [Join Channel](https://t.me/{CHANNEL_USERNAME})\n"
            "Then press /start again.",
            disable_web_page_preview=True
        )

# --- Handle .txt Files ---
@bot.on_message(filters.document & filters.private)
async def txt_file_handler(client: Client, message: Message):
    user_id = message.from_user.id

    # Check verification from MongoDB
    if not verified_users.find_one({"user_id": user_id}):
        return await message.reply_text("❌ You are not verified. Join the channel and send /start again.")

    doc = message.document
    if doc.mime_type != "text/plain":
        return await message.reply_text("⚠️ Please send a valid `.txt` file only.")

    try:
        file_path = await client.download_media(doc)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        preview = content[:4000]  # Telegram limit
        await message.reply_text(f"📄 Content of your file:\n\n{preview}")
    except Exception as e:
        await message.reply_text("⚠️ Failed to read the file.")
        print(f"[ERROR] File read error: {e}")
    finally:
        try:
            os.remove(file_path)
        except Exception:
            pass

# --- Run the Bot ---
if __name__ == "__main__":
    print("✅ Bot is starting...")
    bot.run()
