from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import *

from .buttons import *
from .messages import *
from settings import *
# from AI.ai1 import generate_from_text, generate_from_image
from AI.ai import describe_photo, generate_photo
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
        await log_deleter(user_id=user_id, type="temp", context=context)
        await log_deleter(user_id=user_id, type="cache", context=context)
        context.user_data.setdefault("cache", []).append(msg.message_id)
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
                    len(user.get("saved")["items"])
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

    if message == "Shablon🔥":
            try:
                index = user.get("user_index")
                templates = prompt_get(table="templates")
                template = templates[index]

                msg = await update.message.reply_photo(
                    photo=template.get("file_id"),
                    caption=template_mes.format(
                        template.get("name"),
                        template.get("price"),
                        index+1,
                        len(templates),
                        BOT_USERNAME
                    ),
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(template_but)
                )
                upd(table="users", user_id=user_id, data={"stage": "templates"})
                await log_deleter(type="cache", user_id=user_id, context=context)
            except:
                pass

    if stage == "waiting_prompt":
        
        msg = await update.message.reply_text(text=waiting_mes, parse_mode=ParseMode.HTML)
        photo = generate_photo(message) 
        await context.bot.delete_message(chat_id=user_id, message_id=msg.message_id)
        msg = await update.message.reply_photo(photo=photo, 
                                         caption=free_image_mes.format(message), 
                                         parse_mode=ParseMode.HTML,
                                         reply_markup=InlineKeyboardMarkup(photo_but))

        upd(table="users", user_id=user_id, data={"stage": "waiting_another_prompt", "uniq_id": msg.message_id})

    if stage == "waiting_another_prompt":
        uniq_id = int(user.get("uniq_id", 0))

        msg = await update.message.reply_text(text=waiting_mes, parse_mode=ParseMode.HTML)
        photo_url = generate_photo(message)


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
        await log_deleter(user_id=user_id, type="temp", context=context)
        await log_deleter(user_id=user_id, type="cache", context=context)
        context.user_data.setdefault("cache", []).append(msg.message_id)
        upd(table="users", user_id=user_id, data={"stage": "start"})

        return     

    if query.data == "save":
        saved = user.get("saved")["items"]
        file_id = query.message.photo[-1].file_id

        try:
            prompt = re.search(r"(?im)^\s*📌\s*Prompt\s*:\s*(.+?)\s*$", query.message.caption)
            prompt.group(1).strip() if prompt else ""
            prompt = prompt.group().replace("📌 Prompt: ", "")
        except:
            prompt = " "

        try:
            add_saved_item(user_id=user_id, file_id=file_id, prompt=prompt, amount=0.0)
            await query.answer("Saqlandi✅", show_alert=True)
        except:
            pass
        
    if query.data == "use":
        templates = prompt_get(table="templates")
        template = templates[index]
        balance = user.get("balance")

        if stage == "photo_for_template":
            msg = await query.message.reply_text(
                text=enough_balance_mes,
                parse_mode=ParseMode.HTML
            )
            await log_deleter(type="temp", user_id=user_id, context=context)


        if balance >= template.get("price"):
            msg = await query.message.reply_text(
                text=enough_balance_mes,
                parse_mode=ParseMode.HTML
            )
            await log_adder(type="temp", msg_id=msg.message_id, context=context)
            upd(table="users", user_id=user_id, data={"stage": "photo_for_template"})
        else:
            await query.answer(text=not_enough_mes, show_alert=True)
        await log_adder(type="temp", msg_id=msg.message_id, context=context)

    if "prev" in query.data or "next" in query.data:

        if stage == "templates" or stage == "photo_for_template":
            index = user.get("user_index")
            saved = prompt_get(table="templates")

        if stage == "saved":
            index = user.get("saved_index")

        if query.data == "prev_saved" or query.data == "prev_template":
            if index > 0:
                index-=1
            else:
                index = len(saved)-1
            
        if query.data == "next_saved" or query.data == "next_template":
            if index < len(saved)-1:
                index+=1
            else:
                index=0
        photo=saved[index]

        await query.edit_message_media(
            media=InputMediaPhoto(photo["file_id"])
        )

        if stage == "saved":
            await query.edit_message_caption(
                caption=saved_images_mes.format(
                photo["prompt"],
                photo["amount"],
                index+1,
                len(user.get("saved")["items"])
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(saved_images_but)
            )
            upd(table="users", user_id=user_id, data={"saved_index": index})
        
        if stage == "templates" or stage == "photo_for_template":
            await query.edit_message_caption(
                caption=template_mes.format(
                    photo["name"],
                    photo["price"],
                    index+1,
                    len(saved),
                    BOT_USERNAME
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(template_but)
            )
            await log_deleter(type="temp", user_id=user_id, context=context)
            upd(table="users", user_id=user_id, data={"user_index": index, "stage": "templates"})

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

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user = get(table="users", user_id=user_id)
    stage = user.get("stage")
    template = prompt_get(table="templates")[user.get("user_index")]

    if stage == "photo_for_template":

        msgi = await update.message.reply_text(text=waiting_mes, parse_mode=ParseMode.HTML)
        photo_file = await update.message.photo[-1].get_file()

        file_path = f"AI/temp_{update.message.message_id}.jpg"

        await photo_file.download_to_drive(file_path)

        try:
            result = describe_photo(
                filename=file_path,
                prompt=template.get("prompt")
            )

            msg = await update.message.reply_photo(
                photo=generate_photo(result['text']),
                caption=template_image_mes.format(
                    user.get("balance"),
                    BOT_USERNAME
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(photo_but)
            )

            await context.bot.delete_message(chat_id=user_id, message_id=msgi.message_id)
            await log_adder(type="cache", msg_id=update.message.message_id, context=context)
            await log_adder(type="cache", msg_id=msg.message_id, context=context)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)