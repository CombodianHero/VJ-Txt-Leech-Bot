
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
import random
import asyncio

# ---------------------- Configuration ----------------------
API_ID = 21705536  # Replace with your API ID
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"  # Replace with your API HASH
BOT_TOKEN = "7740653447:AAFbJ_iAr__2LgYO0TZIDkle81CUsayj4us"  # Replace with your bot token
MONGO_DB_URI = "mongodb+srv://engineersbabuxtract:ETxVh71rTNDpmHaj@cluster0.kofsig4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace with your MongoDB URI
CHANNEL = "Engineersbabuupdates"  # e.g., "@mychannel"

# ---------------------- MongoDB Setup ----------------------
mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client["telegram_bot"]
subscribers_collection = db["subscribers"]

async def save_subscriber(user_id: int):
    await subscribers_collection.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id}},
        upsert=True
    )

# ---------------------- Utility Functions ----------------------
async def send_random_photo():
    # Replace with your own list or logic
    photos = [
        "https://i.postimg.cc/4N69wBLt/hat-hacker.webp",
        "https://i.postimg.cc/4N69wBLt/hat-hacker.webp"
    ]
    return random.choice(photos)

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

async def join_channel_if_needed(bot: Client, m: Message):
    if not await check_channel_membership(bot, m):
        await m.reply_text(
            "<b><u>Please join our channel to access this feature.</u></b>",
            reply_markup=join_user()
        )
        return False
    return True

# ---------------------- Message Constants ----------------------
START_MESSAGE = """
👋 Hello {},

Welcome to the bot! You're successfully verified ✅.
"""

# ---------------------- Bot Setup ----------------------
bot = Client(
    "MyBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------------- Handlers ----------------------
@bot.on_message(filters.command("start") & filters.private)
async def start_msg(bot, m: Message):
    user_id = m.chat.id
    await save_subscriber(user_id)

    if not await join_channel_if_needed(bot, m):
        return

    user_mention = m.from_user.mention if m.from_user else "User"

    try:
        photo = await send_random_photo()
        await bot.send_photo(
            chat_id=m.chat.id,
            photo=photo,
            caption=START_MESSAGE.format(user_mention),
            reply_markup=join_user()
        )
    except Exception:
        await m.reply_text(
            f"👋 Welcome {user_mention}!\n\nSomething went wrong while sending the welcome photo.",
            reply_markup=join_user()
        )

# ---------------------- Start the Bot ----------------------
if __name__ == "__main__":
    print("Bot is running...")
    bot.run()
