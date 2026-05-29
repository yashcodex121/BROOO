# ═══════════════════════════════════════════════════════════════
#   🎵 Music Downloader Bot — Main Module
#   Heroku Deployable | Pyrogram v2 + yt-dlp + ffmpeg
# ═══════════════════════════════════════════════════════════════

import asyncio
import os
import subprocess
import time
import logging
import sys
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional

import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, MessageNotModified

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    OWNER_ID,
    FORCE_SUB_CHANNELS,
    UPDATE_CHANNEL,
    SUPPORT_GROUP,
    LOG_CHANNEL,
    DOWNLOAD_DIR,
)


# ═══════════════════════════════════════════════════════════════
#  LOGGER SETUP
# ═══════════════════════════════════════════════════════════════

class BotLogger:
    def __init__(self, name: str = "MusicBot"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        self.logger.addHandler(ch)
        
        # File handler
        os.makedirs("logs", exist_ok=True)
        fh = logging.FileHandler(f"logs/bot_{datetime.now():%Y%m%d}.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
        ))
        self.logger.addHandler(fh)
        
        # Error file handler
        eh = logging.FileHandler(f"logs/error_{datetime.now():%Y%m%d}.log", encoding="utf-8")
        eh.setLevel(logging.ERROR)
        eh.setFormatter(fh.formatter)
        self.logger.addHandler(eh)
    
    def debug(self, msg, *a, **kw): self.logger.debug(msg, *a, **kw)
    def info(self, msg, *a, **kw): self.logger.info(msg, *a, **kw)
    def warning(self, msg, *a, **kw): self.logger.warning(msg, *a, **kw)
    def error(self, msg, *a, **kw): self.logger.error(msg, *a, **kw)
    def critical(self, msg, *a, **kw): self.logger.critical(msg, *a, **kw)

logger = BotLogger("MusicBot")


# ═══════════════════════════════════════════════════════════════
#  FONT HELPER
# ═══════════════════════════════════════════════════════════════

def stylish(text: str, style: str = "bold") -> str:
    mapping = {
        "bold": {
            "A":"𝐀","B":"𝐁","C":"𝐂","D":"𝐃","E":"𝐄","F":"𝐅","G":"𝐆","H":"𝐇",
            "I":"𝐈","J":"𝐉","K":"𝐊","L":"𝐋","M":"𝐌","N":"𝐍","O":"𝐎","P":"𝐏",
            "Q":"𝐐","R":"𝐑","S":"𝐒","T":"𝐓","U":"𝐔","V":"𝐕","W":"𝐖","X":"𝐗",
            "Y":"𝐘","Z":"𝐙","a":"𝐚","b":"𝐛","c":"𝐜","d":"𝐝","e":"𝐞","f":"𝐟",
            "g":"𝐠","h":"𝐡","i":"𝐢","j":"𝐣","k":"𝐤","l":"𝐥","m":"𝐦","n":"𝐧",
            "o":"𝐨","p":"𝐩","q":"𝐪","r":"𝐫","s":"𝐬","t":"𝐭","u":"𝐮","v":"𝐯",
            "w":"𝐰","x":"𝐱","y":"𝐲","z":"𝐳","0":"𝟎","1":"𝟏","2":"𝟐","3":"𝟑",
            "4":"𝟒","5":"𝟓","6":"𝟔","7":"𝟕","8":"𝟖","9":"𝟗",
        },
        "italic": {
            "A":"𝘈","B":"𝘉","C":"𝘊","D":"𝘋","E":"𝘌","F":"𝘍","G":"𝘎","H":"𝘏",
            "I":"𝘐","J":"𝘑","K":"𝘒","L":"𝘓","M":"𝘔","N":"𝘕","O":"𝘖","P":"𝘗",
            "Q":"𝘘","R":"𝘙","S":"𝘚","T":"𝘛","U":"𝘜","V":"𝘝","W":"𝘞","X":"𝘟",
            "Y":"𝘠","Z":"𝘡","a":"𝘢","b":"𝘣","c":"𝘤","d":"𝘥","e":"𝘦","f":"𝘧",
            "g":"𝘨","h":"𝘩","i":"𝘪","j":"𝘫","k":"𝘬","l":"𝘭","m":"𝘮","n":"𝘯",
            "o":"𝘰","p":"𝘱","q":"𝘲","r":"𝘳","s":"𝘴","t":"𝘵","u":"𝘶","v":"𝘷",
            "w":"𝘸","x":"𝘹","y":"𝘺","z":"𝘻",
        },
        "mono": {
            "A":"𝙰","B":"𝙱","C":"𝙲","D":"𝙳","E":"𝙴","F":"𝙵","G":"𝙶","H":"𝙷",
            "I":"𝙸","J":"𝙹","K":"𝙺","L":"𝙻","M":"𝙼","N":"𝙽","O":"𝙾","P":"𝙿",
            "Q":"𝚀","R":"𝚁","S":"𝚂","T":"𝚃","U":"𝚄","V":"𝚅","W":"𝚆","X":"𝚇",
            "Y":"𝚈","Z":"𝚉","a":"𝚊","b":"𝚋","c":"𝚌","d":"𝚍","e":"𝚎","f":"𝚏",
            "g":"𝚐","h":"𝚑","i":"𝚒","j":"𝚓","k":"𝚔","l":"𝚕","m":"𝚖","n":"𝚗",
            "o":"𝚘","p":"𝚙","q":"𝚚","r":"𝚛","s":"𝚜","t":"𝚝","u":"𝚞","v":"𝚟",
            "w":"𝚠","x":"𝚡","y":"𝚢","z":"𝚣",
        },
        "smallcaps": {
            "A":"ᴀ","B":"ʙ","C":"ᴄ","D":"ᴅ","E":"ᴇ","F":"ғ","G":"ɢ","H":"ʜ",
            "I":"ɪ","J":"ᴊ","K":"ᴋ","L":"ʟ","M":"ᴍ","N":"ɴ","O":"ᴏ","P":"ᴘ",
            "Q":"ǫ","R":"ʀ","S":"s","T":"ᴛ","U":"ᴜ","V":"ᴠ","W":"ᴡ","X":"x",
            "Y":"ʏ","Z":"ᴢ","a":"ᴀ","b":"ʙ","c":"ᴄ","d":"ᴅ","e":"ᴇ","f":"ғ",
            "g":"ɢ","h":"ʜ","i":"ɪ","j":"ᴊ","k":"ᴋ","l":"ʟ","m":"ᴍ","n":"ɴ",
            "o":"ᴏ","p":"ᴘ","q":"ǫ","r":"ʀ","s":"s","t":"ᴛ","u":"ᴜ","v":"ᴠ",
            "w":"ᴡ","x":"x","y":"ʏ","z":"ᴢ",
        },
    }
    result = []
    sm = mapping.get(style, mapping["bold"])
    for char in text:
        result.append(sm.get(char, char))
    return "".join(result)


# ═══════════════════════════════════════════════════════════════
#  BOT CLIENT
# ═══════════════════════════════════════════════════════════════

app = Client(
    "MusicDownloaderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

WELCOME_IMAGE = "https://telegra.ph/file/your-welcome-banner.jpg"  # CHANGE THIS


# ═══════════════════════════════════════════════════════════════
#  LOG SENDER
# ═══════════════════════════════════════════════════════════════

async def send_log_event(event_type: str, details: dict):
    if not LOG_CHANNEL:
        return
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    templates = {
        "user_start": (
            f"👤 **USER STARTED BOT**\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: `{details['user_id']}`\n"
            f"👤 Name: {details['first_name']}\n"
            f"📛 Username: @{details.get('username', 'None')}\n"
            f"🌐 Lang: {details.get('lang', 'N/A')}\n"
            f"⏰ Time: `{ts}`"
        ),
        "song_download": (
            f"🎵 **SONG DOWNLOADED**\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👤 User: [{details['first_name']}](tg://user?id={details['user_id']})\n"
            f"🆔 ID: `{details['user_id']}`\n"
            f"🎶 Song: {details['title']}\n"
            f"📀 Mode: {details['mode']}\n"
            f"📏 Size: {details.get('size', 'N/A')}\n"
            f"⏰ Time: `{ts}`"
        ),
        "error": (
            f"❌ **ERROR**\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👤 User: `{details.get('user_id', 'N/A')}`\n"
            f"⚠️ Error: `{details.get('error', 'Unknown')}`\n"
            f"⏰ Time: `{ts}`"
        ),
    }
    
    text = templates.get(event_type, f"📋 Event: {event_type}\nDetails: `{details}`\n⏰ {ts}")
    try:
        await app.send_message(LOG_CHANNEL, text, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Log failed: {e}")


# ═══════════════════════════════════════════════════════════════
#  FORCE SUB
# ═══════════════════════════════════════════════════════════════

async def is_user_joined(client: Client, user_id: int) -> bool:
    if not FORCE_SUB_CHANNELS:
        return True
    for ch in FORCE_SUB_CHANNELS:
        try:
            m = await client.get_chat_member(ch, user_id)
            if m.status in ("left", "kicked", "banned"):
                return False
        except:
            return False
    return True


async def force_sub_button(user_id: int) -> InlineKeyboardMarkup:
    btns = []
    for ch in FORCE_SUB_CHANNELS:
        try:
            chat = await app.get_chat(ch)
            t = chat.title or "Join Channel"
            btns.append([InlineKeyboardButton(f"☞ {stylish(t,'bold')} ☜",
                         url=chat.invite_link or f"https://t.me/{chat.username}")])
        except:
            btns.append([InlineKeyboardButton(f"☞ {stylish('Join Channel','bold')} ☜",
                         url=f"https://t.me/{ch}")])
    btns.append([InlineKeyboardButton(f"🔄 {stylish('Check Again','mono')} 🔄",
                 callback_data="refresh_membership")])
    return InlineKeyboardMarkup(btns)


# ═══════════════════════════════════════════════════════════════
#  START MESSAGE & KEYBOARDS
# ═══════════════════════════════════════════════════════════════

def start_text(name: str) -> str:
    return (f"✨ **{stylish('WELCOME TO','bold')}** ✨\n\n"
            f"╔══════════════════╗\n"
            f"║   🎵 **{stylish('MUSIC DOWNLOADER','italic')}** 🎵\n"
            f"╚══════════════════╝\n\n"
            f"{stylish('Hey','smallcaps')} **{stylish(name,'bold')}**! 👋\n\n"
            f"{stylish('I am a powerful music downloading bot.','mono')}\n\n"
            f"🎯 **{stylish('What I Can Do','bold')}**\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🎵 → {stylish('Download songs from YouTube','smallcaps')}\n"
            f"🎚️ → {stylish('Choose audio mode: Lofi, Normal, Bass, ECO','smallcaps')}\n"
            f"📀 → {stylish('High Quality 320kbps MP3','smallcaps')}\n"
            f"🖼️ → {stylish('Thumbnail with music file','smallcaps')}\n"
            f"🔍 → {stylish('Inline search (any chat)','smallcaps')}\n\n"
            f"💡 **{stylish('How To Use','bold')}**\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"✧ {stylish('Send me a song name or YT link','smallcaps')}\n"
            f"✧ {stylish('Choose a mode from below','smallcaps')}\n"
            f"✧ {stylish('Or use inline:@bot song','smallcaps')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🙏 **{stylish('Thank you for using me!','italic')}** 🎧")


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔍 {stylish('Search Song','bold')}",
                              switch_inline_query_current_chat=""),
         InlineKeyboardButton(f"🎚️ {stylish('Modes','bold')}",
                              callback_data="show_modes")],
        [InlineKeyboardButton(f"📈 {stylish('Trending','italic')}",
                              callback_data="trending"),
         InlineKeyboardButton(f"❓ {stylish('Help','italic')}",
                              callback_data="help")],
        [InlineKeyboardButton(f"📢 {stylish('Updates','mono')}",
                              url=f"https://t.me/{UPDATE_CHANNEL.lstrip('@')}"),
         InlineKeyboardButton(f"💬 {stylish('Support','mono')}",
                              url=f"https://t.me/{SUPPORT_GROUP.lstrip('@')}")],
        [InlineKeyboardButton(f"✨ {stylish('Inline Mode','bold')} ✨",
                              switch_inline_query="")],
        [InlineKeyboardButton(f"📤 {stylish('Share Bot','smallcaps')} 📤",
                              url="https://t.me/share/url?url=https://t.me/YourBotUsername")],
    ])


def modes_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🎧 {stylish('Lofi','bold')}", callback_data="mode_lofi"),
         InlineKeyboardButton(f"🎸 {stylish('Bass','bold')}", callback_data="mode_bass")],
        [InlineKeyboardButton(f"🎵 {stylish('Normal','italic')}", callback_data="mode_normal")],
        [InlineKeyboardButton(f"🪞 {stylish('Eco','mono')}", callback_data="mode_eco")],
        [InlineKeyboardButton(f"🔙 {stylish('Back','smallcaps')}", callback_data="home")],
    ])


# ═══════════════════════════════════════════════════════════════
#  SONG DOWNLOADER (yt-dlp + ffmpeg)
# ═══════════════════════════════════════════════════════════════

async def download_song(query: str, mode: str = "normal",
                        user_id: int = 0, first_name: str = "User") -> Optional[dict]:
    ts = int(time.time())
    outtmpl = os.path.join(DOWNLOAD_DIR, f"{ts}_%(title)s.%(ext)s")
    thumb_local = os.path.join(DOWNLOAD_DIR, f"{ts}_thumb.jpg")
    
    audio_filters = {
        "lofi":   "lowpass=f=4000,volume=0.85,equalizer=f=200:t=q:w=1:g=3",
        "bass":   "bass=g=10,f=100,w=0.5,loudnorm=I=-14:TP=-2:LRA=11",
        "normal": None,
        "eco":    "aecho=0.8:0.7:60:0.4,aecho=0.6:0.4:150:0.3,volume=0.9",
    }
    filt = audio_filters.get(mode)
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "writethumbnail": True,
        "embedthumbnail": True,
        "addmetadata": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"},
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail"},
        ],
    }
    if filt:
        ydl_opts["postprocessor_args"] = ["-af", filt]
    
    try:
        logger.info(f"Downloading '{query}' | Mode: {mode} | User: {user_id}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)
            if not info or "entries" not in info:
                raise Exception("No results")
            entry = info["entries"][0]
            title = entry.get("title", "Unknown")
            duration = entry.get("duration", 0)
            thumbnail = entry.get("thumbnail", "")
            uploader = entry.get("uploader", "Unknown")
            dur_str = f"{duration//60}:{duration%60:02d}" if duration else "N/A"
            
            # Find downloaded file
            fp = None
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(str(ts)) and f.endswith(".mp3"):
                    fp = os.path.join(DOWNLOAD_DIR, f)
                    break
            if not fp or not os.path.exists(fp):
                mp3s = sorted([os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".mp3")],
                              key=os.path.getmtime, reverse=True)
                if mp3s: fp = mp3s[0]
                else: raise Exception("File not found")
            
            size_mb = os.path.getsize(fp) / (1024*1024)
            
            # Download thumbnail locally
            tp = None
            if thumbnail:
                try:
                    r = requests.get(thumbnail, timeout=10)
                    if r.status_code == 200:
                        tp = thumb_local
                        with open(tp, "wb") as f: f.write(r.content)
                except: pass
            
            logger.info(f"OK: '{title}' | {size_mb:.1f}MB | {mode}")
            await send_log_event("song_download", {
                "user_id": user_id, "first_name": first_name,
                "title": title, "mode": mode, "size": f"{size_mb:.1f} MB",
            })
            
            return {
                "file_path": fp, "title": title, "duration": dur_str,
                "thumbnail": thumbnail, "thumb_path": tp,
                "uploader": uploader, "size": size_mb,
            }
    except Exception as e:
        logger.error(f"Download failed for '{query}': {e}")
        await send_log_event("error", {"user_id": user_id, "error": str(e)})
        return None


async def cleanup(*paths):
    for p in paths:
        if p and os.path.exists(p):
            try: os.remove(p)
            except: pass


# ═══════════════════════════════════════════════════════════════
#  HANDLERS
# ═══════════════════════════════════════════════════════════════

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    uid = message.from_user.id
    name = message.from_user.first_name or "User"
    logger.info(f"/start by {name} ({uid})")
    await send_log_event("user_start", {
        "user_id": uid, "first_name": name,
        "username": message.from_user.username or "None",
        "lang": message.from_user.language_code or "N/A",
    })
    if not await is_user_joined(client, uid):
        await message.reply_photo(WELCOME_IMAGE,
            caption=f"⚠️ **{stylish('Please join our channels first!','bold')}** ⚠️\n\n{stylish('You must join all channels to use this bot.','smallcaps')}",
            reply_markup=await force_sub_button(uid))
        return
    kb = start_keyboard()
    if uid == OWNER_ID:
        kb.inline_keyboard.append([InlineKeyboardButton(f"👑 {stylish('Owner Panel','bold')} 👑", callback_data="owner_panel")])
    await message.reply_photo(WELCOME_IMAGE, caption=start_text(name), reply_markup=kb)


@app.on_message(filters.command(["song", "music", "download", "play"]))
async def song_handler(client, message):
    uid = message.from_user.id
    if not await is_user_joined(client, uid):
        await message.reply_text(f"⚠️ **{stylish('Please join first!','bold')}**", reply_markup=await force_sub_button(uid))
        return
    if len(message.text.split()) < 2:
        await message.reply_text(f"🎵 **{stylish('Usage','bold')}:**\n\n`/song <name or link>`\n{stylish('Example:','smallcaps')} `/song faded alan walker`")
        return
    query = message.text.split(" ", 1)[1]
    msg = await message.reply_text(
        f"🎚️ **{stylish('Select Audio Mode','bold')}**\n\n🔍 {stylish('Song:','smallcaps')} **{query}**\n\n{stylish('Choose a mode to proceed:','italic')}",
        reply_markup=modes_keyboard())
    if not hasattr(app, "_song_map"): app._song_map = {}
    app._song_map[msg.id] = {"query": query, "uid": uid, "name": message.from_user.first_name or "User"}


@app.on_message(filters.text & filters.private & ~filters.command([]))
async def text_handler(client, message):
    uid = message.from_user.id
    if not await is_user_joined(client, uid): return
    query = message.text.strip()
    if len(query) < 2: return
    msg = await message.reply_text(
        f"🎚️ **{stylish('Select Audio Mode','bold')}**\n\n🔍 {stylish('Song:','smallcaps')} **{query}**\n\n{stylish('Choose a mode to proceed:','italic')}",
        reply_markup=modes_keyboard())
    if not hasattr(app, "_song_map"): app._song_map = {}
    app._song_map[msg.id] = {"query": query, "uid": uid, "name": message.from_user.first_name or "User"}


@app.on_message(filters.command("help"))
async def help_handler(client, message):
    await message.reply_photo(WELCOME_IMAGE, caption=(
        f"╔══════════════════════╗\n║   **{stylish('HELP CENTER','bold')}**   ║\n╚══════════════════════╝\n\n"
        f"🎯 **{stylish('Commands','bold')}**\n━━━━━━━━━━━━━━━━━━\n"
        f"▸ `/start` — {stylish('Start bot','smallcaps')}\n"
        f"▸ `/song <name>` — {stylish('Download song','smallcaps')}\n"
        f"▸ `/help` — {stylish('This message','smallcaps')}\n"
        f"▸ `/about` — {stylish('About bot','smallcaps')}\n\n"
        f"💡 **{stylish('Inline','bold')}**\n`@bot <song>` {stylish('in any chat','smallcaps')}\n\n"
        f"🎚️ **{stylish('Modes','bold')}**\n🎧 Lofi | 🎸 Bass | 🎵 Normal | 🪞 Eco"
    ), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"🔙 {stylish('Back To Home','bold')}", callback_data="home")]]))


@app.on_message(filters.command("about"))
async def about_handler(client, message):
    await message.reply_photo(WELCOME_IMAGE, caption=(
        f"╔══════════════════════╗\n║   **{stylish('ABOUT','bold')}**   ║\n╚══════════════════════╝\n\n"
        f"🎵 **{stylish('Music Downloader Bot','italic')}**\n\n"
        f"📌 Version: **3.0.0**\n⚡ Framework: **Pyrogram v2 + yt-dlp**\n🐍 Language: **Python 3.11+**\n\n"
        f"👑 **Owner**: [**Owner**](tg://user?id={OWNER_ID})\n"
        f"📢 **Updates**: @{UPDATE_CHANNEL.lstrip('@')}\n"
        f"💬 **Support**: @{SUPPORT_GROUP.lstrip('@')}\n\n"
        f"{stylish('Thank you! 🙏','italic')}"
    ), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"🔙 {stylish('Back To Home','bold')}", callback_data="home")]]))


# ═══════════════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLER
# ═══════════════════════════════════════════════════════════════

@app.on_callback_query()
async def callback_handler(client, callback):
    data = callback.data
    uid = callback.from_user.id
    name = callback.from_user.first_name or "User"
    
    if not await is_user_joined(client, uid):
        await callback.message.edit_caption(
            caption=f"⚠️ **{stylish('Please join first!','bold')}**",
            reply_markup=await force_sub_button(uid))
        await callback.answer("⚠️ Join channels first!", show_alert=True)
        return
    
    # ── HOME ──
    if data == "home":
        kb = start_keyboard()
        if uid == OWNER_ID:
            kb.inline_keyboard.append([InlineKeyboardButton(f"👑 {stylish('Owner Panel','bold')} 👑", callback_data="owner_panel")])
        try: await callback.message.edit_caption(caption=start_text(name), reply_markup=kb)
        except MessageNotModified: pass
        await callback.answer()
    
    # ── SHOW MODES ──
    elif data == "show_modes":
        txt = (f"🎚️ **{stylish('AUDIO MODES','bold')}** 🎚️\n\n"
               f"{stylish('Choose your preferred sound:','smallcaps')}\n\n"
               f"🎧 **Lofi** — {stylish('Chill, low-fi vibes','smallcaps')}\n"
               f"🎸 **Bass** — {stylish('Boosted bass','smallcaps')}\n"
               f"🎵 **Normal** — {stylish('Original quality','smallcaps')}\n"
               f"🪞 **Eco** — {stylish('Echo effect','smallcaps')}")
        try: await callback.message.edit_caption(caption=txt, reply_markup=modes_keyboard())
        except MessageNotModified: pass
        await callback.answer()
    
    # ── MODE SELECT ──
    elif data.startswith("mode_"):
        mode = data.replace("mode_", "")
        mid = callback.message.id
        if not hasattr(app, "_song_map"): app._song_map = {}
        
        if mid in app._song_map:
            si = app._song_map.pop(mid)
            if uid != si["uid"]:
                await callback.answer("❌ Not your request!", show_alert=True)
                return
            
            await callback.message.edit_caption(
                caption=(f"⏳ **{stylish('Processing...','bold')}**\n\n"
                         f"🎵 Song: **{si['query']}**\n🎚️ Mode: **{stylish(mode.capitalize(),'bold')}**\n\n"
                         f"⬇️ {stylish('Downloading and processing...','italic')}"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"⏳ {stylish('Please wait...','mono')}", callback_data="ignore")]]))
            
            result = await download_song(si["query"], mode, uid, si["name"])
            
            if result and result["file_path"]:
                await callback.message.delete()
                cap = (f"🎵 **{stylish(result['title'],'bold')}**\n━━━━━━━━━━━━━━\n"
                       f"🎚️ Mode: {stylish(mode.capitalize(),'bold')}\n"
                       f"⏱️ Duration: {result['duration']}\n"
                       f"📀 Quality: 320kbps 🔥\n"
                       f"📏 Size: {result['size']:.1f} MB\n"
                       f"━━━━━━━━━━━━━━\n🙏 **{stylish('Thanks for using!','italic')}** 🎧")
                await client.send_audio(
                    chat_id=uid,
                    audio=result["file_path"],
                    thumb=result["thumb_path"] if result["thumb_path"] else None,
                    title=result["title"],
                    performer=result.get("uploader", "Unknown"),
                    caption=cap,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"🔍 {stylish('Search Again','bold')}", switch_inline_query_current_chat=""),
                         InlineKeyboardButton(f"🎚️ {stylish('Change Mode','bold')}", callback_data="show_modes")],
                        [InlineKeyboardButton(f"🏠 {stylish('Home','smallcaps')}", callback_data="home")],
                    ]))
                await cleanup(result["file_path"], result.get("thumb_path"))
            else:
                await callback.message.edit_caption(
                    caption=f"❌ **{stylish('Failed to download!','bold')}**\n\n{stylish('Please try a different song name.','smallcaps')}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"🏠 {stylish('Home','smallcaps')}", callback_data="home")]]))
        else:
            # Mode preview from home
            desc = {
                "lofi": f"🎧 **{stylish('Lofi Mode','bold')}**\n\n{stylish('A gentle, chill experience','italic')}\n━━━━━━━━━━━━━━━\n🎚️ Low-pass filter applied\n🎛️ Warm and soft sound\n🎯 Perfect for relaxation",
                "bass": f"🎸 **{stylish('Bass Boost Mode','bold')}**\n\n{stylish('Pump up the bass!','italic')}\n━━━━━━━━━━━━━━━\n🎚️ Bass gain +10dB @ 100Hz\n🎛️ Sub frequencies enhanced\n🎯 Perfect for EDM, Hip-Hop",
                "normal": f"🎵 **{stylish('Normal Mode','bold')}**\n\n{stylish('Original Quality','italic')}\n━━━━━━━━━━━━━━━\n🎚️ No audio filters\n🎛️ Clean and pure sound\n🎯 Best for casual listening",
                "eco": f"🪞 **{stylish('Eco Mode','bold')}**\n\n{stylish('Feel the space!','italic')}\n━━━━━━━━━━━━━━━\n🎚️ Echo / reverb effect added\n🎛️ Ambient and atmospheric\n🎯 Perfect for melodic songs",
            }
            await callback.message.edit_caption(caption=desc.get(mode, "Unknown"), reply_markup=modes_keyboard())
        await callback.answer()
    
    # ── OTHER ──
    elif data == "trending":
        await callback.answer("📈 Trending feature coming soon!", show_alert=True)
    elif data == "help":
        await callback.message.edit_caption(
            caption=(f"╔══════════════════════╗\n║   **{stylish('HELP CENTER','bold')}**   ║\n╚══════════════════════╝\n\n"
                     f"🎯 **{stylish('Commands','bold')}**\n━━━━━━━━━━━━━━━━━━\n"
                     f"▸ `/start` — {stylish('Start bot','smallcaps')}\n"
                     f"▸ `/song <name>` — {stylish('Download song','smallcaps')}\n"
                     f"▸ `/help` — {stylish('This message','smallcaps')}\n"
                     f"▸ `/about` — {stylish('About bot','smallcaps')}\n\n"
                     f"💡 **{stylish('Inline','bold')}**\n`@bot <song>` {stylish('in any chat','smallcaps')}\n\n"
                     f"🎚️ **{stylish('Modes','bold')}**\n🎧 Lofi | 🎸 Bass | 🎵 Normal | 🪞 Eco"),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"🔙 {stylish('Back To Home','bold')}", callback_data="home")]]))
        await callback.answer()
    elif data == "about":
        await callback.message.edit_caption(
            caption=(f"╔══════════════════════╗\n║   **{stylish('ABOUT','bold')}**   ║\n╚══════════════════════╝\n\n"
                     f"🎵 **{stylish('Music Downloader Bot','italic')}**\n\n"
                     f"📌 Version: **3.0.0**\n⚡ Framework: **Pyrogram v2 + yt-dlp**\n🐍 Language: **Python 3.11+**\n\n"
                     f"👑 **Owner**: [**Owner**](tg://user?id={OWNER_ID})\n"
                     f"📢 **Updates**: @{UPDATE_CHANNEL.lstrip('@')}\n"
                     f"💬 **Support**: @{SUPPORT_GROUP.lstrip('@')}\n\n"
                     f"{stylish('Thank you! 🙏','italic')}"),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"🔙 {stylish('Back To Home','bold')}", callback_data="home")]]))
        await callback.answer()
    elif data == "refresh_membership":
        if await is_user_joined(client, uid):
            kb = start_keyboard()
            if uid == OWNER_ID:
                kb.inline_keyboard.append([InlineKeyboardButton(f"👑 {stylish('Owner Panel','bold')} 👑", callback_data="owner_panel")])
            await callback.message.edit_caption(caption=start_text(name), reply_markup=kb)
            await callback.answer("✅ Thanks for joining! Enjoy 🎵")
        else:
            await callback.answer("❌ You haven't joined all channels yet!", show_alert=True)
    elif data == "owner_panel":
        if uid == OWNER_ID:
            await callback.message.edit_caption(
                caption=(f"👑 **{stylish('OWNER PANEL','bold')}** 👑\n\n"
                         f"📊 **Bot Status**: 🟢 **{stylish('Running','mono')}**\n━━━━━━━━━━━━━━━━\n\n"
                         f"⚙️ **{stylish('Quick Actions','bold')}**\n"
                         f"▸ {stylish('Monitor logs','smallcaps')}\n"
                         f"▸ {stylish('Check server health','smallcaps')}\n"
                         f"▸ {stylish('Manage force sub','smallcaps')}\n\n"
                         f"{stylish('More features coming soon..','italic')}"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"🔙 {stylish('Back To Home','bold')}", callback_data="home")]]))
        else:
            await callback.answer("🚫 You are not the owner!", show_alert=True)
    elif data == "ignore":
        await callback.answer()
    else:
        await callback.answer("❓ Unknown", show_alert=True)


# ═══════════════════════════════════════════════════════════════
#  INLINE MODE
# ═══════════════════════════════════════════════════════════════

@app.on_inline_query()
async def inline_handler(client, query):
    string = query.query.strip()
    uid = query.from_user.id
    if not await is_user_joined(client, uid):
        await query.answer([], switch_pm_text="⚠️ Join channels first!", switch_pm_parameter="start", cache_time=0)
        return
    if not string:
        await query.answer([], switch_pm_text="🔍 Type a song name!", switch_pm_parameter="start", cache_time=0)
        return
    
    results = [InlineQueryResultArticle(
        title=f"🎧 {stylish('Lofi','bold')} — {string}",
        description=f"{stylish('Chill low-fi version','smallcaps')}",
        input_message_content=InputTextMessageContent(f"/song {string}"),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"⬇️ {stylish('Download Lofi','bold')}", callback_data=f"inline_dl_lofi|{string}")]]),
    ), InlineQueryResultArticle(
        title=f"🎸 {stylish('Bass','bold')} — {string}",
        description=f"{stylish('Boosted bass version','smallcaps')}",
        input_message_content=InputTextMessageContent(f"/song {string}"),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"⬇️ {stylish('Download Bass','bold')}", callback_data=f"inline_dl_bass|{string}")]]),
    ), InlineQueryResultArticle(
        title=f"🎵 {stylish('Normal','italic')} — {string}",
        description=f"{stylish('Original quality','smallcaps')}",
        input_message_content=InputTextMessageContent(f"/song {string}"),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"⬇️ {stylish('Download Normal','bold')}", callback_data=f"inline_dl_normal|{string}")]]),
    ), InlineQueryResultArticle(
        title=f"🪞 {stylish('Eco','mono')} — {string}",
        description=f"{stylish('Echo effect','smallcaps')}",
        input_message_content=InputTextMessageContent(f"/song {string}"),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"⬇️ {stylish('Download Eco','bold')}", callback_data=f"inline_dl_eco|{string}")]]),
    )]
    await query.answer(results, cache_time=1, is_personal=False)


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"🎵 {stylish('Music Downloader Bot','bold')} starting...")
    print(f"👑 Owner ID: {OWNER_ID}")
    print(f"📢 Channel: @{UPDATE_CHANNEL.lstrip('@')}")
    app.run()
