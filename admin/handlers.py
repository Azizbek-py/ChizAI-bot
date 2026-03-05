from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Admin panelga xush kelibsiz ✅")

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Admin: text qabul qilindi")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text("Admin: button")

async def document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Admin: document qabul qilindi")