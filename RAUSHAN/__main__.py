import random
import os
import logging
import asyncio
from pyrogram import enums
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus, ChatType
from pyrogram.types import ChatPermissions
from flask import Flask
from threading import Thread
from pymongo import MongoClient, errors
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait, UserNotParticipant, RPCError
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton,CallbackQuery
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
    return "Shivi Bot is Running!"

def run_flask():
    app_web.run(host="0.0.0.0", port=8080)

# Config vars
API_ID = int(os.getenv("API_ID","14050586"))
API_HASH = os.getenv("API_HASH","42a60d9c657b106370c79bb0a8ac560c")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME","rishu_musicbot")
MONGO_URI = os.getenv("MONGO_URI","mongodb+srv://Krishna:pss968048@cluster0.4rfuzro.mongodb.net/?retryWrites=true&w=majority")
OWNER_ID = int(os.getenv("OWNER_ID","5738579437"))
FORCE_JOIN1 = os.getenv("FORCE_JOIN1","RishuApi")
FORCE_JOIN2 = os.getenv("FORCE_JOIN2","rishucoder")

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
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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


STICKERS = [
    "CAACAgUAAxkBAAENygtnrrVXr5zEE-h_eiG8lRUkRkMwfwACExMAAjRk6VbUUzZjByHDfzYE",  # Sticker 1
    "CAACAgUAAxkBAAENyglnrrUIPfP95UfP7Tg2GAz8b_mbBAACHAsAAgFTKFR6GWIrt0FPfTYE",  # Sticker 2
    "CAACAgUAAxkBAAENygdnrrSuukBGTLd_k2q-kPf80pPMqgAClw0AAmdr-Fcu4b8ZzcizqDYE",  # Sticker 3
    "CAACAgUAAxkBAAENygtnrrVXr5zEE-h_eiG8lRUkRkMwfwACExMAAjRk6VbUUzZjByHDfzYE",  # Sticker 4
    "CAACAgUAAxkBAAENyglnrrUIPfP95UfP7Tg2GAz8b_mbBAACHAsAAgFTKFR6GWIrt0FPfTYE"   # Sticker 5
]

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
                [InlineKeyboardButton("🍬Join 🍬", url=f"https://t.me/{FORCE_JOIN1}")],
                [InlineKeyboardButton("🍬 Join 🍬", url=f"https://t.me/{FORCE_JOIN2}")],
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

    # ✅ **Send a random sticker from the list with error handling**
    try:
        random_sticker = random.choice(STICKERS)  # Ensure STICKERS is a valid list
        await message.reply_sticker(random_sticker)
    except Exception as e:
        print(f"Sticker send failed: {e}")  # Debugging: Check if sticker is invalid

    await asyncio.sleep(1)

    # ✅ **Ensure progress message is deleted even if sticker fails**
    try:
        await baby.delete()
    except Exception as e:
        print(f"Failed to delete progress message: {e}")

    # ✅ **MongoDB Check & Insert New User Only Once**
    try:
        existing_user = users_col.find_one({"_id": user_id})  # Check if user exists

        if not existing_user:
            users_col.insert_one({"_id": user_id, "username": user.username})
            total_users = users_col.count_documents({})  # Count total users

            # ✅ **Send notification to owner only for new users**
            await bot.send_message(
                OWNER_ID, 
                f"**New User Alert!**\n👤 **User:** {user.mention}\n"
                f"🆔 **ID:** `{user_id}`\n📛 **Username:** {username}\n"
                f"📊 **Total Users:** `{total_users}`"
            )

    except Exception as e:
        print(f"MongoDB Error: {e}")

    # Main Start Message
    await message.reply_photo(
        photo="https://files.catbox.moe/qej5mx.jpg",
        caption=f"""**✦ » ʜᴇʏ {user.mention}**
**✦ » ᴛʜɪs ɪs ᴀ sɪᴍᴘʟᴇ ʙᴀɴ ᴀʟʟ ʙᴏᴛ ᴡʜɪᴄʜ ɪs ʙᴀsᴇᴅ ᴏɴ ᴘʏʀᴏɢʀᴀᴍ ʟɪʙʀᴀʀʏ.**

**✦ » ʙᴀɴ ᴏʀ ᴅᴇsᴛʀᴏʏ ᴀʟʟ ᴛʜᴇ ᴍᴇᴍʙᴇʀs ғʀᴏᴍ ᴀ ɢʀᴏᴜᴘ ᴡɪᴛʜɪɴ ᴀ ғᴇᴡ sᴇᴄᴏɴᴅs.**

**✦ » ᴄʜᴇᴄᴋ ᴍʏ ᴀʙɪʟɪᴛʏ, ɢɪᴠᴇ ᴍᴇ ғᴜʟʟ ᴘᴏᴡᴇʀs ᴀɴᴅ ᴛʏᴘᴇ `/banall` ᴛᴏ ꜱᴇᴇ ᴍᴀɢɪᴄ ɪɴ ɢʀᴏᴜᴘ.**""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✙ ʌᴅᴅ ϻє ɪη ʏσυʀ ɢʀσυᴘ ✙", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [InlineKeyboardButton("˹ sυᴘᴘσʀᴛ ˼", url="http://t.me/rishu1286"),
             InlineKeyboardButton("˹ υᴘᴅᴧᴛєs ˼", url="http://t.me/ur_rishu_143")],
            [InlineKeyboardButton("˹ ʜєʟᴘ ᴧηᴅ ᴄσϻϻᴧηᴅ | ᴍσʀє ɪηғσ ˼", callback_data="help_main")]
        ])
    )

@bot.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    await query.answer()  # Callback properly acknowledge karega

    # ✅ Force Join Check
    if query.data == "check_force":
        user_id = query.from_user.id
        if await check_force_join(user_id):
            await query.message.edit_text("✅ **You have joined! Now you can use the bot.**")
        else:
            await query.answer("❌ You haven't joined both channels yet!", show_alert=True)
        return

    # ✅ Help Menu Handling
    elif query.data == "help_main":
        await query.message.edit_text(
            "**🔹 Help Menu 🔹**\n\nChoose a category below to get more details:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("˹ ʙᴧsɪᴄ ˼", callback_data="help_basic"),
                 InlineKeyboardButton("˹ ᴧᴅϻɪη ˼", callback_data="help_admin")],
                [InlineKeyboardButton("˹ ᴧᴅᴠᴧηᴄє ˼", callback_data="help_advanced")],
                [InlineKeyboardButton("⌯ ʙᴧᴄᴋ ⌯", callback_data="back_to_start")]
            ])
        )

    elif query.data == "help_basic":
        await query.message.edit_text(
            "**🛠 Basic Commands:**\n"
            "`/start` - Start the bot\n"
            "`/help` - Show this help menu\n"
            "`/info` - Get your user info\n"
            "`/about` - Know about the bot",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⌯ ʙᴧᴄᴋ ⌯", callback_data="help_main")]
            ])
        )

    elif query.data == "help_admin":
        await query.message.edit_text(
            "**🔒 Admin Commands:**\n"
            "`/ban` - Ban a user\n"
            "`/unban` - Unban a user\n"
            "`/mute` - Mute a user\n"
            "`/unmute` - Unmute a user\n"
            "`/unpin` - Unpin a message",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⌯ ʙᴧᴄᴋ ⌯", callback_data="help_main")]
            ])
        )

    elif query.data == "help_advanced":
        await query.message.edit_text(
            "**⚙️ Advanced Features:**\n"
            "`/banall` - Ban all members in a group\n"
            "`/unbanall` - Unban all members\n"
            "`/muteall` - Mute all members\n"
            "`/unmuteall` - Unmute all members\n"
            "`/broadcast` - Send a message to all users",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⌯ ʙᴧᴄᴋ ⌯", callback_data="help_main")]
            ])
        )

    elif query.data == "back_to_start":
        user = query.from_user
        await query.message.edit_text(
            f"""**✦ » ʜᴇʏ {user.mention}**
**✦ » ᴛʜɪs ɪs ᴀ sɪᴍᴘʟᴇ ʙᴀɴ ᴀʟʟ ʙᴏᴛ ᴡʜɪᴄʜ ɪs ʙᴀsᴇᴅ ᴏɴ ᴘʏʀᴏɢʀᴀᴍ ʟɪʙʀᴀʀʏ.**

**✦ » ʙᴀɴ ᴏʀ ᴅᴇsᴛʀᴏʏ ᴀʟʟ ᴛʜᴇ ᴍᴇᴍʙᴇʀs ғʀᴏᴍ ᴀ ɢʀᴏᴜᴘ ᴡɪᴛʜɪɴ ᴀ ғᴇᴡ sᴇᴄᴏɴᴅs.**

**✦ » ᴄʜᴇᴄᴋ ᴍʏ ᴀʙɪʟɪᴛʏ, ɢɪᴠᴇ ᴍᴇ ғᴜʟʟ ᴘᴏᴡᴇʀs ᴀɴᴅ ᴛʏᴘᴇ `/banall` ᴛᴏ ꜱᴇᴇ ᴍᴀɢɪᴄ ɪɴ ɢʀᴏᴜᴘ.**""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✙ ʌᴅᴅ ϻє ɪη ʏσυʀ ɢʀσυᴘ ✙", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
                [InlineKeyboardButton("˹ sυᴘᴘσʀᴛ ˼", url="http://t.me/rishu1286"),
                 InlineKeyboardButton("˹ υᴘᴅᴧᴛєs ˼", url="http://t.me/ur_rishu_143")],
                [InlineKeyboardButton("˹ ʜєʟᴘ ᴧηᴅ ᴄσϻϻᴧηᴅ | ᴍσʀє ɪηғσ ˼", callback_data="help_main")]
            ])
        )

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

@bot.on_message(filters.command("kickall") & filters.group)
async def kickall_command(client, message: Message):
    chat_id = message.chat.id
    bot_member = await client.get_chat_member(chat_id, client.me.id)

    # ✅ Bot ke paas kick permissions hai ya nahi
    if not bot_member.privileges or not bot_member.privileges.can_restrict_members:
        return await message.reply_text("❌ **I don't have permission to kick members!**")

    kicked_count = 0
    failed_count = 0

    async for member in client.get_chat_members(chat_id):
        # ❌ Skip: Bots & Admins ko kick nahi karega
        if member.user.is_bot or member.status in ["administrator", "creator"]:
            continue  

        try:
            await client.ban_chat_member(chat_id, member.user.id)
            await client.unban_chat_member(chat_id)
            kicked_count += 1
        except Exception as e:
            failed_count += 1
            logging.error(f"Failed to kick {member.user.id}: {e}")

    # ✅ Final Summary Message
    await message.reply_text(f"✅ **Successfully kicked {kicked_count} members!**\n❌ **Failed: {failed_count}**")

@bot.on_message(filters.command("muteall") & filters.group)
async def muteall_command(client, message):
    chat_id = message.chat.id
    bot_member = await client.get_chat_member(chat_id, client.me.id)

    # ✅ Bot ke paas mute permissions hai ya nahi
    if not bot_member.privileges or not bot_member.privileges.can_restrict_members:
        return await message.reply_text("❌ **I don't have permission to mute members!**")

    muted_count = 0
    failed_count = 0

    async for member in client.get_chat_members(chat_id):
        # ❌ Skip: Bots & Admins ko mute nahi karega
        if member.user.is_bot or member.status in ["administrator", "creator"]:
            continue  

        try:
            await client.restrict_chat_member(chat_id, member.user.id, ChatPermissions(can_send_messages=False))
            muted_count += 1
        except Exception as e:
            failed_count += 1
            logging.error(f"Failed to mute {member.user.id}: {e}")

    # ✅ Final Summary Message
    await message.reply_text(f"✅ **Successfully muted {muted_count} members!**\n❌ **Failed: {failed_count}**")

@bot.on_message(filters.command("unbanall") & filters.group)
async def unbanall_command(client, message):
    chat_id = message.chat.id
    bot_member = await client.get_chat_member(chat_id, client.me.id)

    # ✅ Bot ke paas unban permissions hai ya nahi
    if not bot_member.privileges or not bot_member.privileges.can_restrict_members:
        return await message.reply_text("❌ **I don't have permission to unban members!**")

    unbanned_count = 0
    failed_count = 0

    async for member in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.BANNED):
        try:
            await client.unban_chat_member(chat_id, member.user.id)
            unbanned_count += 1
        except Exception as e:
            failed_count += 1
            logging.error(f"Failed to unban {member.user.id}: {e}")

    # ✅ Final Summary Message
    await message.reply_text(f"✅ **Successfully unbanned {unbanned_count} members!**\n❌ **Failed: {failed_count}**")

@app.on_message(filters.command("unpinall") & filters.group)
async def unpin_all(client, message):
    chat_id = message.chat.id
    bot_member = await client.get_chat_member(chat_id, client.me.id)

    # ✅ Check: Bot ke paas unpin permissions hai ya nahi
    if not bot_member.privileges or not bot_member.privileges.can_pin_messages:
        return await message.reply_text("❌ **I don't have permission to unpin messages!**")

    try:
        await client.unpin_all_chat_messages(chat_id)
        await message.reply_text("✅ **Successfully unpinned all messages in this group!**")
    except Exception as e:
        logging.error(f"Error in unpin_all: {e}")
        await message.reply_text("❌ **Failed to unpin messages.**")

@app.on_message(filters.command("unmuteall") & filters.group)
async def unmute_all(client, message):
    chat_id = message.chat.id
    bot_member = await client.get_chat_member(chat_id, BOT_ID)

    # ✅ Check: Bot ke paas restrict permission hai ya nahi
    if not bot_member.privileges or not bot_member.privileges.can_restrict_members:
        return await message.reply_text("❌ **I don't have permission to unmute members!**")

    unmuted_count = 0
    failed_count = 0

    async for member in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.RESTRICTED):
        try:
            await client.restrict_chat_member(
                chat_id, 
                member.user.id, 
                ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_polls=True,
                    can_add_web_page_previews=True,
                    can_invite_users=True
                )
            )
            unmuted_count += 1
        except Exception as e:
            failed_count += 1
            print(f"❌ Failed to unmute {member.user.id}: {e}")

    # ✅ Final Message (Summary)
    await message.reply_text(f"✅ **Successfully unmuted {unmuted_count} members!**\n❌ **Failed: {failed_count}**")

@bot.on_message(filters.command("ping"))
async def ping_command(client, message: Message):
    start = time()
    reply = await message.reply_text("🏓 **Pinging...**")
    end = time()
    await reply.edit_text(f"🏓 **Pong!**\n📡 **Latency:** `{round((end - start) * 1000)}ms`")

@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message):
    if not message.reply_to_message:
        return await message.reply_text("**Reply to a message to broadcast!**")
    
    users = db.users.find()  # MongoDB se sab users ka data le raha hai
    sent_count = 0
    failed_count = 0

    for user in users:
        try:
            await message.reply_to_message.copy(user["user_id"])
            sent_count += 1
            await asyncio.sleep(0.5)  # Spam avoid karne ke liye
        except Exception as e:
            failed_count += 1
            print(f"Failed to send message to {user['user_id']}: {e}")

    await message.reply_text(f"✅ **Broadcast Sent Successfully!**\n📩 Sent: {sent_count}\n❌ Failed: {failed_count}")

@bot.on_message(filters.command("restart") & filters.user(OWNER_ID))
async def restart_command(client, message: Message):
    await message.reply_text("🔄 **Restarting bot...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

# Start Flask in a separate thread
Thread(target=run_flask).start()

# Start bot
try:
    bot.start()
    logging.info("Shivi Bot is Running!")
    idle()
except Exception as e:
    logging.error(f"Bot failed to start: {e}")
