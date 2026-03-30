import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from settings import BOT_TOKEN
from common.dispatch import *

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CallbackQueryHandler(button))
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

if __name__ == "__main__":
    print("Polling ishlayapti...")
    app.run_polling(
        allowed_updates=[Update.MESSAGE, Update.CALLBACK_QUERY],
        drop_pending_updates=True,
    )