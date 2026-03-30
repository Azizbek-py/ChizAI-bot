from telegram import Update
from telegram.ext import ContextTypes
from common.roles import is_admin

from user.handlers import start as user_start, text as user_text, button as user_button, photo as user_photo
from admin.handlers import start as admin_start, text as admin_text, button as admin_button, photo as admin_photo


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else None
    if is_admin(uid):
        return await admin_start(update, context)
    return await user_start(update, context)


async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else None
    if is_admin(uid):
        return await admin_text(update, context)
    return await user_text(update, context)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else None
    if is_admin(uid):
        return await admin_button(update, context)
    return await user_button(update, context)


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else None
    if is_admin(uid):
        return await admin_photo(update, context)
    return await user_photo(update, context)

