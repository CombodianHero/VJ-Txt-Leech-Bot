from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from functools import wraps
import random

# -------------------- Configuration --------------------
API_ID = 21705536  # Replace with your API ID
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"  # Replace with your API HASH
BOT_TOKEN = "7740653447:AAFbJ_iAr__2LgYO0TZIDkle81CUsayj4us"  # Replace with your bot token
MONGO_DB_URI = "mongodb+srv://engineersbabuxtract:ETxVh71rTNDpmHaj@cluster0.kofsig4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace with your Mongo URI
CHANNEL = "Engineersbabuupdates"  # e.g., "@mychannel" or "mychannel"

# -------------------- Bot & DB Setup --------------------
bot = Client("MyBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client["telegram_bot"]
subscribers_collection = db["subscribers"]

# -------------------- Save Subscriber --------------------
async def save_subscriber(user_id: int):
    await subscribers_collection.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id}},
        upsert=True
    )

# -------------------- Channel Join Check --------------------
def join_user():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL.strip('@')}")]
    ])

async def check_channel_membership(bot: Client, m: Message):
    try:
        member = await bot.get_chat_member(CHANNEL, m.chat.id)
        if member.status in ["left", "kicked"]:
            return False
    except:
        return False
    return True

def require_channel_join(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        if not await check_channel_membership(client, message):
            await message.reply_text(
                "<b><u>Please join our channel to use this feature.</u></b>",
                reply_markup=join_user()
            )
            return
        return await func(client, message)
    return wrapper

# -------------------- Random Welcome Photo --------------------
async def send_random_photo():
    photos = [
        "https://i.postimg.cc/4N69wBLt/hat-hacker.webp",
        "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"
    ]
    return random.choice(photos)

# -------------------- Start Command --------------------
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(bot, m: Message):
    user_id = m.chat.id
    await save_subscriber(user_id)

    user_mention = m.from_user.mention if m.from_user else "User"
    try:
        photo = await send_random_photo()
        await bot.send_photo(
            chat_id=m.chat.id,
            photo=photo,
            caption=f"👋 Hello {user_mention},\n\nWelcome to the bot! You're successfully verified ✅.",
            reply_markup=join_user()
        )
    except:
        await m.reply_text(
            f"👋 Welcome {user_mention}!\n\n(⚠️ Failed to send welcome image)",
            reply_markup=join_user()
        )

# -------------------- Restricted Commands --------------------
@bot.on_message(filters.command("Appx") & filters.private)
@require_channel_join
async def appx_handler(bot, message: Message):
    await message.reply_text("✅ You accessed /Appx command.")

@bot.on_message(filters.command("cp") & filters.private)
@require_channel_join
async def cp_handler(bot, message: Message):
    await message.reply_text("✅ You accessed /cp command.")

@bot.on_message(filters.command("pw") & filters.private)
@require_channel_join
async def pw_handler(bot, message: Message):
    await message.reply_text("✅ You accessed /pw command.")

# -------------------- Restrict Everything Else --------------------
@bot.on_message(
    (filters.document | filters.video | filters.audio | filters.photo | filters.text | filters.txt)
    & filters.private
    & ~filters.command(["start"])
)
@require_channel_join
async def all_other_handler(bot, message: Message):
    await message.reply_text("📥 Message or file received!")

# -------------------- Run Bot --------------------
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.run()
