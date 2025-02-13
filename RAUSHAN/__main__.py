import os
import logging
import asyncio
from flask import Flask
from threading import Thread
from pymongo import MongoClient, errors
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait, UserNotParticipant, RPCError
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from time import time
import sys

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Flask app
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "BanAll Bot is Running!"

def run_flask():
    app_web.run(host="0.0.0.0", port=8080)

# Config vars
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = int(os.getenv("OWNER_ID"))
FORCE_JOIN1 = os.getenv("FORCE_JOIN1")
FORCE_JOIN2 = os.getenv("FORCE_JOIN2")

# MongoDB setup
try:
    client = MongoClient(MONGO_URI)
    db = client["banall_bot"]
    users_col = db["users"]
except errors.ConnectionFailure as e:
    logging.error(f"Failed to connect to MongoDB: {e}")
    sys.exit(1)

# Pyrogram bot
bot = Client(
    "banall",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

async def check_force_join(user_id):
    """Check if the user is a member of both required channels."""
    try:
        await bot.get_chat_member(FORCE_JOIN1, user_id)
        await bot.get_chat_member(FORCE_JOIN2, user_id)
        return True
    except UserNotParticipant:
        return False
    except RPCError as e:
        logging.warning(f"Error checking force join for {user_id}: {e}")
        return False

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    user = message.from_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "No Username"

    # Force join check
    if not await check_force_join(user_id):
        return await message.reply_text(
            "**❌ You must join our channels first!**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔹 Join Channel 1", url=f"https://t.me/{FORCE_JOIN1}")],
                [InlineKeyboardButton("🔸 Join Channel 2", url=f"https://t.me/{FORCE_JOIN2}")],
                [InlineKeyboardButton("✅ I Joined", callback_data="check_force")]
            ])
        )

    # Start progress animation
    baby = await message.reply_text("[□□□□□□□□□□] 0%")
    progress = [
        "[■□□□□□□□□□] 10%", "[■■□□□□□□□□] 20%", "[■■■□□□□□□□] 30%",
        "[■■■■□□□□□□] 40%", "[■■■■■□□□□□] 50%", "[■■■■■■□□□□] 60%",
        "[■■■■■■■□□□] 70%", "[■■■■■■■■□□] 80%", "[■■■■■■■■■□] 90%",
        "[■■■■■■■■■■] 100%"
    ]
    for step in progress:
        await baby.edit_text(f"**{step}**")
        await asyncio.sleep(0.2)

    await baby.edit_text("**❖ Jᴀʏ Sʜʀᴇᴇ Rᴀᴍ 🚩...**")
    await asyncio.sleep(2)
    await baby.delete()

    # Save user in MongoDB
    try:
        if not users_col.find_one({"_id": user_id}):
            users_col.insert_one({"_id": user_id, "username": user.username})
            await bot.send_message(
                OWNER_ID, 
                f"**New User Alert!**\n👤 **User:** {user.mention}\n"
                f"🆔 **ID:** `{user_id}`\n📛 **Username:** {username}"
            )
    except errors.PyMongoError as e:
        logging.error(f"MongoDB Error: {e}")

    # Main Start Message
    await message.reply_photo(
        photo="https://files.catbox.moe/qej5mx.jpg",
        caption=f"""**✦ » ʜᴇʏ {user.mention}**
**✦ » ᴛʜɪs ɪs ᴀ sɪᴍᴘʟᴇ ʙᴀɴ ᴀʟʟ ʙᴏᴛ ᴡʜɪᴄʜ ɪs ʙᴀsᴇᴅ ᴏɴ ᴘʏʀᴏɢʀᴀᴍ ʟɪʙʀᴀʀʏ.**

**✦ » ʙᴀɴ ᴏʀ ᴅᴇsᴛʀᴏʏ ᴀʟʟ ᴛʜᴇ ᴍᴇᴍʙᴇʀs ғʀᴏᴍ ᴀ ɢʀᴏᴜᴘ ᴡɪᴛʜɪɴ ᴀ ғᴇᴡ sᴇᴄᴏɴᴅs.**

**✦ » ᴄʜᴇᴄᴋ ᴍʏ ᴀʙɪʟɪᴛʏ, ɢɪᴠᴇ ᴍᴇ ғᴜʟʟ ᴘᴏᴡᴇʀs ᴀɴᴅ ᴛʏᴘᴇ `/banall` ᴛᴏ ꜱᴇᴇ ᴍᴀɢɪᴄ ɪɴ ɢʀᴏᴜᴘ.**""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚜️ Aᴅᴅ ᴍᴇ Bᴀʙʏ ⚜️", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [InlineKeyboardButton("🔸 Oᴡɴᴇʀ 🔸", url="http://t.me/rishu1286")],
            [InlineKeyboardButton("▫️ Uᴘᴅᴀᴛᴇs ▫️", url="http://t.me/ur_rishu_143")]
        ])
    )

@bot.on_callback_query()
async def callback_handler(client, query):
    if query.data == "check_force":
        user_id = query.from_user.id
        if await check_force_join(user_id):
            await query.message.edit_text("✅ **You have joined! Now you can use the bot.**")
        else:
            await query.answer("❌ You haven't joined both channels yet!", show_alert=True)

@bot.on_message(filters.command("banall") & filters.group)
async def banall_command(client, message: Message):
    chat_id = message.chat.id
    admin = await bot.get_chat_member(chat_id, message.from_user.id)

    if admin.status not in ["administrator", "creator"]:
        return await message.reply_text("❌ **You need to be an admin to use this command!**")

    if not admin.can_restrict_members:
        return await message.reply_text("❌ **I need Ban Members permission to perform this action!**")

    await message.reply_text("🔖 **Starting Backloli Process...**")
    
    count = 0
    failed = 0
    async for member in bot.get_chat_members(chat_id):
        try:
            if member.user.id != message.from_user.id and member.user.id != bot.me.id:
                await bot.ban_chat_member(chat_id, member.user.id)
                count += 1
        except Exception as e:
            failed += 1

    await message.reply_text(f"✅ **Banned {count} members!**\n❌ **Failed: {failed}**")


@bot.on_message(filters.command("ping"))
async def ping_command(client, message: Message):
    start = time()
    reply = await message.reply_text("🏓 **Pinging...**")
    end = time()
    await reply.edit_text(f"🏓 **Pong!**\n📡 **Latency:** `{round((end - start) * 1000)}ms`")

@bot.on_message(filters.command("restart") & filters.user(OWNER_ID))
async def restart_command(client, message: Message):
    await message.reply_text("🔄 **Restarting bot...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

# Start Flask in a separate thread
Thread(target=run_flask).start()

# Start bot
try:
    bot.start()
    logging.info("BanAll Bot is Running!")
    idle()
except Exception as e:
    logging.error(f"Bot failed to start: {e}")