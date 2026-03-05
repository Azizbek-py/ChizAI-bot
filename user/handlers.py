from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import *

from .buttons import *
from .messages import *
from AI.ai import photo_generation
import asyncio
from contextlib import suppress
from telegram.error import BadRequest

async def _loading_dots(bot, chat_id: int, stop: asyncio.Event, text: str = "Rasm chizilmoqda"):
    msg = await bot.send_message(chat_id=chat_id, text=f"{text}.")
    dots = [".", "..", "..."]
    i = 0
    try:
        while not stop.is_set():
            i = (i + 1) % 3
            try:
                await msg.edit_text(f"{text}{dots[i]}")
            except BadRequest as e:
                # "Message is not modified" va shunga o'xshashlarini tinch o'tkazib yuboramiz
                if "message is not modified" not in str(e).lower():
                    pass
            await asyncio.sleep(0.7)
    finally:
        with suppress(BadRequest):
            await msg.delete()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.message.chat_id
    await update.message.reply_text(text=start_mes, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardMarkup(start_but, resize_keyboard=True))
    insert(table="users", user_id=user_id, data={
        "Name": update.message.from_user.full_name,
        "index": 0,
        "username": update.message.from_user.username,
        "stage": "start"
    })

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user = get(table="users", user_id=user_id)
    stage = user["stage"]
    message=update.message.text


    if message == "Ortga🔙":
        await update.message.reply_text(
            text=main_menu_mes,
            parse_mode=ParseMode.HTML,
            reply_markup=ReplyKeyboardMarkup(start_but, resize_keyboard=True)
        )
        upd(table="users", user_id=user_id, data={"stage": "start"})

    if message == "Rasm Yaratish🪄":
        await update.message.reply_text(
            text=create_photo_mes,
            parse_mode=ParseMode.HTML,
            reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
        )
        upd(table="users", user_id=user_id, data={"stage": "waiting_prompt"})

    if stage == "waiting_prompt":
        
        msg = await update.message.reply_text(text=waiting_mes)
        photo = await photo_generation(message) 
        await context.bot.delete_message(chat_id=user_id, message_id=msg.message_id)
        await update.message.reply_photo(photo=photo)

    users = get(table="users")
    
    print(users)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ...

async def document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ...