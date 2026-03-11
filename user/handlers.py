from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import *

from .buttons import *
from .messages import *
from AI.ai import photo_generation
import asyncio
import re
from contextlib import suppress
from telegram.error import BadRequest

async def log_deleter(user_id, type, context):
    messages = context.user_data.get(type, [])

    for msg_id in messages:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=msg_id)
        except:
            pass

async def log_adder(type, context, msg_id):
    context.user_data.setdefault(str(type), []).append(msg_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.message.chat_id
    msg = await update.message.reply_text(text=start_mes, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardMarkup(start_but, resize_keyboard=True))
    insert(table="users", user_id=user_id, data={
        "Name": update.message.from_user.full_name,
        "index": 0,
        "username": update.message.from_user.username,
        "stage": "start"
    })

    await log_deleter(user_id=user_id, type="start_messages", context=context)
    await log_deleter(user_id=user_id, type="messages", context=context)

    context.user_data.setdefault("start_messages", []).append(msg.message_id)
    context.user_data.setdefault("start_messages", []).append(update.message.message_id)

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user = get(table="users", user_id=user_id)
    stage = user["stage"]
    message=update.message.text
    msg = []

    users = get(table="users")


    if message == "Ortga🔙":
        msg = await update.message.reply_text(
            text=main_menu_mes,
            parse_mode=ParseMode.HTML,
            reply_markup=ReplyKeyboardMarkup(start_but, resize_keyboard=True)
        )
        
        context.user_data.setdefault("messages", []).append(update.message.message_id)
        await log_deleter(user_id=user_id, type="messages", context=context)
        context.user_data.setdefault("messages", []).append(msg.message_id)
        upd(table="users", user_id=user_id, data={"stage": "start"})

        return
    
    if message == "Rasm Yaratish🪄":
        msg = await update.message.reply_text(
            text=create_photo_mes,
            parse_mode=ParseMode.HTML,
            reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
        )
        upd(table="users", user_id=user_id, data={"stage": "waiting_prompt"})

    if message == "Rasmlarim🗂":
        saved = user.get("saved")["items"]
        index = user.get("saved_index", 0)
        try:
            photo = saved[index]    
            msg = await update.message.reply_photo(
                photo=photo["file_id"],
                caption=saved_images_mes.format(
                    photo["prompt"],
                    photo["amount"],
                    index+1,
                    len(user.get("saved"))
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(saved_images_but)
            )
            upd(table="users", user_id=user_id, data={"stage": "saved"})
        except:
            msg = await update.message.reply_text(
                text=not_saved_mes,
                parse_mode=ParseMode.HTML,
                reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
            )
            # await log_deleter(type="saved_messages", context=context, user_id=user_id)
            # await log_adder(type="saved_messages", context=context, msg_id=msg.message_id)
            # await log_adder(type="saved_messages", context=context, msg_id=update.message.message_id)
            
    if stage == "waiting_prompt":
        
        msg = await update.message.reply_text(text=waiting_mes)
        photo = await photo_generation(message) 
        await context.bot.delete_message(chat_id=user_id, message_id=msg.message_id)
        msg = await update.message.reply_photo(photo=photo, 
                                         caption=free_image_mes.format(message), 
                                         parse_mode=ParseMode.HTML,
                                         reply_markup=InlineKeyboardMarkup(photo_but))

        upd(table="users", user_id=user_id, data={"stage": "waiting_another_prompt", "uniq_id": msg.message_id})

    if stage == "waiting_another_prompt":
        uniq_id = int(user.get("uniq_id", 0))

        msg = await update.message.reply_text(text=waiting_mes)
        photo_url = await photo_generation(message)


        await context.bot.edit_message_media(
            chat_id=update.effective_chat.id,
            message_id=uniq_id,
            media=InputMediaPhoto(media=photo_url),
        )

        await context.bot.edit_message_caption(
            chat_id=update.effective_chat.id,
            message_id=uniq_id,
            caption=free_image_mes.format(message),
            reply_markup=InlineKeyboardMarkup(photo_but),
            parse_mode=ParseMode.HTML
        )

        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
            await context.bot.delete_message(chat_id=user_id, message_id=update.message.message_id)
        except BadRequest:
            pass

    
    if not msg:
        await log_adder(type="log", context=context, msg_id=update.message.message_id)
        await log_deleter(user_id=user_id, context=context, type="log")
        return

    context.user_data.setdefault("messages", []).append(update.message.message_id)
    context.user_data.setdefault("messages", []).append(msg.message_id)
    
    users = get(table="users")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_chat.id
    user = get(table="users", user_id=user_id)
    saved = user.get("saved")["items"]
    stage = user.get("stage")
    index = user.get("user_index")

    if query.data == "back":
        msg = await query.message.reply_text(
            text=main_menu_mes,
            parse_mode=ParseMode.HTML,
            reply_markup=ReplyKeyboardMarkup(start_but, resize_keyboard=True)
        )
        
        await log_deleter(user_id=user_id, type="messages", context=context)
        context.user_data.setdefault("messages", []).append(msg.message_id)
        upd(table="users", user_id=user_id, data={"stage": "start"})

        return     

    if query.data == "save":
        saved = user.get("saved")["items"]
        file_id = query.message.photo[-1].file_id

        prompt = re.search(r"(?im)^\s*📌\s*Prompt\s*:\s*(.+?)\s*$", query.message.caption)
        prompt.group(1).strip() if prompt else ""

        try:
            add_saved_item(user_id=user_id, file_id=file_id, prompt=prompt.group().replace("📌 Prompt: ", ""), amount=0.0)
            await query.answer("Saqlandi✅", show_alert=True)
        except:
            pass

    if "prev" in query.data or "next" in query.data:

        if stage == "saved":
            index = user.get("saved_index")
            if query.data == "prev_saved":
                if index > 0:
                    index-=1
                else:
                    index = len(saved)-1
            if query.data == "next_saved":
                if index < len(saved)-1:
                    index+=1
                else:
                    index=0
            photo=saved[index]

            await query.edit_message_media(
                media=InputMediaPhoto(photo["file_id"])
            )

            await query.edit_message_caption(
                caption=saved_images_mes.format(
                photo["prompt"],
                photo["amount"],
                index+1,
                len(user.get("saved"))
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(saved_images_but)
            )
            upd(table="users", user_id=user_id, data={"saved_index": index})

    if query.data == "delete":
        index = user.get("saved_index")
        photo = saved[index]

        delete(table="users",user_id=user_id, file_id=photo["file_id"])
        await query.answer("Rasm o'chirildi🗑✔️", show_alert=True)

        saved = get(table="users", user_id=user_id).get("saved")["items"]

        if len(saved) == 0:
            msg = await query.message.reply_text(
                text=main_menu_mes,
                parse_mode=ParseMode.HTML,
                reply_markup=ReplyKeyboardMarkup(start_but, resize_keyboard=True)
            )
            await log_deleter(user_id=user_id, type="messages", context=context)
            await log_adder(context=context, type="messages", msg_id=msg.message_id)
            upd(table="users", user_id=user_id, data={"stage": "start", "saved_index": 0})

async def document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ...