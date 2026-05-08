import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from pydub import AudioSegment

TOKEN = "8586435834:AAF3494SL5UM3HVZPlCKMY2vihu6vetJN30"
ADMIN_ID = 8048066572

users = {}
all_users = set()

# start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    all_users.add(user)

    kb = [
        [InlineKeyboardButton("🎵 ارسال موزیک", callback_data="send_music")],
        [InlineKeyboardButton("📊 آمار", callback_data="stats")]
    ]

    await update.message.reply_text(
        "سلام 👋\nبه ربات ادیت موزیک خوش آمدی 🎧",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# buttons
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "send_music":
        await q.message.reply_text("🎵 موزیک خود را بفرست")

    if q.data == "stats":
        if q.from_user.id == ADMIN_ID:
            await q.message.reply_text(f"👥 تعداد کاربران: {len(all_users)}")
        else:
            await q.message.reply_text("❌ فقط ادمین")

# receive audio
async def audio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id
    file = await update.message.audio.get_file()

    path = f"{user}.mp3"
    await file.download_to_drive(path)

    users[user] = {"file": path}

    kb = [
        [InlineKeyboardButton("✏️ تغییر Artist", callback_data="artist")],
        [InlineKeyboardButton("📝 تغییر Title", callback_data="title")],
        [InlineKeyboardButton("📅 تغییر Year", callback_data="year")],
        [InlineKeyboardButton("🎤 تبدیل به ویس", callback_data="voice")]
    ]

    await update.message.reply_text(
        "یک گزینه انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# edit buttons
async def edit_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    user = q.from_user.id
    await q.answer()

    if user not in users:
        return

    if q.data == "artist":
        users[user]["step"] = "artist"
        await q.message.reply_text("نام خواننده را بفرست")

    elif q.data == "title":
        users[user]["step"] = "title"
        await q.message.reply_text("نام آهنگ را بفرست")

    elif q.data == "year":
        users[user]["step"] = "year"
        await q.message.reply_text("سال آهنگ را بفرست")

    elif q.data == "voice":

        path = users[user]["file"]

        sound = AudioSegment.from_mp3(path)
        voice = f"{user}.ogg"
        sound.export(voice, format="ogg")

        await q.message.reply_voice(open(voice, "rb"))

        os.remove(path)
        os.remove(voice)

        users.pop(user)

# text input
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    if user not in users:
        return

    step = users[user].get("step")
    path = users[user]["file"]

    try:
        audio = MP3(path, ID3=EasyID3)
    except:
        audio = MP3(path)
        audio.add_tags()

    if step == "artist":
        audio["artist"] = update.message.text

    elif step == "title":
        audio["title"] = update.message.text

    elif step == "year":
        audio["date"] = update.message.text

    audio.save()

    await update.message.reply_audio(open(path, "rb"))
    await update.message.reply_text("✅ موزیک ادیت شد")

    os.remove(path)
    users.pop(user)

def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(CallbackQueryHandler(edit_buttons))
    app.add_handler(MessageHandler(filters.AUDIO, audio))
    app.add_handler(MessageHandler(filters.TEXT, text))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
