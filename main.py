from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import UserNotParticipant
import os

# Your credentials
API_ID = "21705536"
API_HASH = "c5bb241f6e3ecf33fe68a444e288de2d"
BOT_TOKEN = "7740653447:AAFbJ_iAr__2LgYO0TZIDkle81CUsayj4us"
FORCE_CHANNEL = "@Engineersbabuupdates"  # Replace with your channel username

app = Client("ForceJoinBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# Function to check if the user is a member of the channel
async def is_user_joined(user_id: int) -> bool:
    try:
        member = await app.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ("member", "administrator", "creator")
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"Error checking user membership: {e}")
        return False


# Start command handler
@app.on_message(filters.command("start") & filters.private)
async def start(client, message: Message):
    user = message.from_user

    if not await is_user_joined(user.id):
        try:
            await message.reply(
                f"Hi {user.mention},\n\nTo use this bot, please **join our channel** first!",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_CHANNEL.strip('@')}")],
                        [InlineKeyboardButton("I've Joined", callback_data="check_join")]
                    ]
                )
            )
        except Exception as e:
            print(f"Error sending force join message: {e}")
        return

    await message.reply("You're verified! Send me a `.txt` file and I'll process it.")


# Callback handler to recheck user membership
@app.on_callback_query(filters.regex("check_join"))
async def recheck_join(client, callback_query):
    user_id = callback_query.from_user.id

    if await is_user_joined(user_id):
        await callback_query.message.edit("You're now verified! Send me a `.txt` file to process.")
    else:
        await callback_query.answer("You're not joined yet!", show_alert=True)


# Handle .txt files
@app.on_message(filters.document & filters.private)
async def handle_txt_file(client, message: Message):
    if not await is_user_joined(message.from_user.id):
        await message.reply("Please join the channel first to use this feature.")
        return

    doc = message.document
    if not doc.file_name.endswith(".txt"):
        await message.reply("Please upload a `.txt` file only.")
        return

    file_path = await doc.download()
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    await message.reply(f"Here is the content of your file:\n\n{content[:4096]}")
    os.remove(file_path)


app.run()
