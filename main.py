import os
import asyncio
import sqlite3
import json

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# ==========================================

bot = Client(
    "vc_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

userbot = Client(
    "vc_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

calls = PyTgCalls(userbot)

# ================= DATABASE =================

DB_NAME = "vc_database.db"

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    data TEXT
)
""")

conn.commit()


def save_user(user_id, data):
    cursor.execute(
        "REPLACE INTO users (user_id, data) VALUES (?, ?)",
        (user_id, json.dumps(data))
    )
    conn.commit()


def get_user(user_id):
    cursor.execute(
        "SELECT data FROM users WHERE user_id = ?",
        (user_id,)
    )

    row = cursor.fetchone()

    if row:
        return json.loads(row[0])

    return None


# ============================================

active_calls = {}

# ================= START ====================

@bot.on_message(filters.command("start") & filters.private)
async def start(_, m: Message):

    save_user(
        m.from_user.id,
        {"step": "group"}
    )

    await m.reply_text(
        "🎵 **Anonymous VC Player**\n\n"
        "Send group username or link:"
    )


# ================= GROUP ====================

@bot.on_message(filters.private & filters.text & ~filters.command("start"))
async def text_handler(_, m: Message):

    uid = m.from_user.id
    user = get_user(uid)

    if not user:
        return await m.reply_text("Use /start")

    if user["step"] == "group":

        txt = m.text

        grp = (
            txt.split("t.me/")[-1]
            if "t.me/" in txt
            else txt.strip("@")
        )

        user["group"] = grp
        user["step"] = "audio"

        save_user(uid, user)

        await m.reply_text(
            f"✅ Group Saved: @{grp}\n\n"
            "Now send audio file."
        )


# ================= AUDIO ====================

@bot.on_message(
    filters.private &
    (filters.audio | filters.voice | filters.document)
)
async def audio_handler(_, m: Message):

    uid = m.from_user.id
    user = get_user(uid)

    if not user or user["step"] != "audio":
        return await m.reply_text("Use /start")

    msg = await m.reply_text("⏳ Downloading audio...")

    try:

        path = f"vc_{uid}.mp3"

        await m.download(file_name=path)

        user["audio"] = path

        save_user(uid, user)

        grp = user["group"]

        await msg.edit_text("⏳ Joining VC...")

        chat = await userbot.get_chat(grp)

        chat_id = chat.id

        await calls.join_group_call(
            chat_id,
            AudioPiped(path)
        )

        active_calls[uid] = chat_id

        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔄 Replay",
                    callback_data="replay"
                ),

                InlineKeyboardButton(
                    "🎵 New",
                    callback_data="new"
                )
            ],
            [
                InlineKeyboardButton(
                    "⏹ Stop",
                    callback_data="stop"
                )
            ]
        ])

        await msg.edit_text(
            f"🎵 Playing in @{grp}",
            reply_markup=kb
        )

    except Exception as e:

        await msg.edit_text(
            f"❌ Error:\n\n{e}"
        )


# ================= REPLAY ====================

@bot.on_callback_query(filters.regex("replay"))
async def replay(_, cb: CallbackQuery):

    uid = cb.from_user.id

    if uid not in active_calls:
        return await cb.answer(
            "No active VC",
            show_alert=True
        )

    user = get_user(uid)

    try:

        chat_id = active_calls[uid]

        await calls.leave_group_call(chat_id)

        await asyncio.sleep(2)

        await calls.join_group_call(
            chat_id,
            AudioPiped(user["audio"])
        )

        await cb.answer("🔄 Replaying")

    except Exception as e:

        await cb.message.reply_text(str(e))


# ================= NEW AUDIO ====================

@bot.on_callback_query(filters.regex("new"))
async def new_audio(_, cb: CallbackQuery):

    uid = cb.from_user.id

    user = get_user(uid)

    try:

        if uid in active_calls:

            await calls.leave_group_call(
                active_calls[uid]
            )

            del active_calls[uid]

    except:
        pass

    if user:

        user["step"] = "audio"

        save_user(uid, user)

    await cb.message.edit_text(
        "Send new audio file."
    )


# ================= STOP ====================

@bot.on_callback_query(filters.regex("stop"))
async def stop(_, cb: CallbackQuery):

    uid = cb.from_user.id

    try:

        if uid in active_calls:

            await calls.leave_group_call(
                active_calls[uid]
            )

            del active_calls[uid]

        await cb.message.edit_text(
            "⏹ VC stopped."
        )

    except Exception as e:

        await cb.message.edit_text(str(e))


# ================= MAIN ====================

async def main():

    await bot.start()
    print("✅ Bot Started")

    await userbot.start()
    print("✅ Userbot Started")

    await calls.start()
    print("✅ PyTgCalls Started")

    print("🎵 VC Bot Running")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
