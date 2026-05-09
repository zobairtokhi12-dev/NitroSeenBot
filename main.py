from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8586435834:AAF3494SL5UM3HVZPlCKMY2vihu6vetJN30"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات روشن شد ✅")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

print("Bot Started")

app.run_polling()
