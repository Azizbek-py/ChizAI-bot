from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from .messages import *
from .buttons import *
from database.db import *
from settings import FIRST_BALANCE

def log_adder(msg_id, context, type):
    context.user_data.setdefault(str(type), []).append(msg_id)
async def log_deletter(user_id, type, context):
    messages = context.user_data.get(str(type), [])

    for msg_id in messages:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=msg_id)
        except:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    insert(table="users", user_id=update.effective_chat.id, data={
        "Name": update.effective_chat.full_name,
        "username": update.effective_chat.username,
        "stage": "start",
        "user_index": 0,
        "saved_index": 0,
        "balance": FIRST_BALANCE,
        "uniq_id": 0
    })

    await update.message.reply_text(
        text=start_mes,
        reply_markup=ReplyKeyboardMarkup(start_but, resize_keyboard=True),
    )

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user = get(table="users", user_id=user_id)
    stage = user.get("stage")
    message = update.message.text
    uniq_id = (user.get("uniq_id"))

    if message == "Ortga🔙":  
        upd(table="users", user_id=user_id, data={
            "stage": "start"
        })

        msg = await update.message.reply_text(
            text=main_menu_mes,
            reply_markup=ReplyKeyboardMarkup(start_but, resize_keyboard=True)
        )
        upd(table="users", user_id=user_id, data={"stage": "start"})
        log_adder(type="messages", msg_id=update.message.message_id, context=context)
        await log_deletter(type="messages", user_id=user_id, context=context)
        await log_deletter(type="caches", user_id=user_id, context=context)
        await log_deletter(type="temp", user_id=user_id, context=context)
        log_adder(type="messages", msg_id=msg.message_id, context=context)
        return
    

    if message == "Shablonlar🗂":
        templates = prompt_get(table="templates")

        if len(templates) != 0:
            user_index = user.get("user_index", 0)

            template = templates[user_index]
            msg = await update.message.reply_photo(
                photo=template.get("file_id"),
                caption=template_mes.format(
                    template.get("name", ""),
                    template.get("price", 0),
                    template.get("prompt", "Prompt"),
                    template.get("created_at", ""),
                    user_index+1,
                    len(templates)
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(template_but)
            )
            upd(table="users", user_id=user_id, data={"uniq_id": template.get("id")})
            log_adder(msg_id=msg.message_id, context=context, type="temp")
            log_adder(msg_id=update.message.message_id, context=context, type="temp")
        else:
            await update.message.reply_text(
                text=no_template_mes,
                reply_markup=ReplyKeyboardMarkup(no_template_but, resize_keyboard=True)
            )

    if message == "Qo'shish➕":
        upd(table="users", user_id=user_id, data={"stage": "get_photo"})

        await update.message.reply_text(
            text=get_photo_mes,
            reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
        )

    if message == "Balans💸":
        upd(table="users", user_id=user_id, data={"stage": "user_info"})

        msg = await update.message.reply_text(
            text=get_user_id_mes,
            reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
        )
        await log_deletter(type="caches", user_id=user_id, context=context)
        log_adder(type="caches", context=context, msg_id=msg.message_id)
        return 
    
    if stage == "user_info":
        try:
            user_info = get(table="users", user_id=int(message))

            msg = await update.message.reply_text(
                text=user_info_mes.format(
                    user_info.get("Name"),
                    user_info.get("username"),
                    user_info.get("balance", 0)
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
            )
            upd(table="users", user_id=user_id, data={"stage": "new_balance", "saved_index": int(message)})
        except:

            msg = await update.message.reply_text(
                text=no_user_info_mes.format(message),
                parse_mode=ParseMode.HTML,
                reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
            )
        log_adder(type="temp", context=context, msg_id=msg.message_id)
        log_adder(type="caches", context=context, msg_id=update.message.message_id)
        return

    if stage == "new_balance":
        user_info = get(table="users", user_id=user.get("saved_index"))

        old_balance = user_info.get("balance")
        if "+" in message:
            new_balance = old_balance+int(message.replace("+", ""))
            msg = await update.message.reply_text(
                text=user_info_mes.format(
                    user_info.get("Name"),
                    user_info.get("username"),
                    new_balance
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
            )
            user_msg = await context.bot.send_message(text=deposit_mes.format(message.replace("+", "")), parse_mode=ParseMode.HTML, chat_id=user.get("saved_index"))
            add_cache(user_id=user.get("saved_index"), value=user_msg.message_id)
            await log_deletter(type="temp", user_id=user_id, context=context)

        if "-" in message:
            new_balance = old_balance-int(message.replace("-", ""))
            msg = await update.message.reply_text(
                text=user_info_mes.format(
                    user_info.get("Name"),
                    user_info.get("username"),
                    new_balance
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
            )
            user_msg = await context.bot.send_message(text=withdrawal_mes.format(message.replace("-", "")), parse_mode=ParseMode.HTML, chat_id=user.get("saved_index"))
            add_cache(user_id=user.get("saved_index"), value=user_msg.message_id)
            await log_deletter(type="temp", user_id=user_id, context=context)
        
        try: #log adder
            log_adder(type="temp", context=context, msg_id=msg.message_id)
        except:
            pass
        
        log_adder(type="cache", context=context, msg_id=update.message.message_id)
        upd(table="users", user_id=user.get("saved_index"), data={"balance"})

    if stage == "get_name":
        prompt_upd(table="templates", id=uniq_id, data={"name": message})
        upd(table="users", user_id=user_id, data={"stage": "get_price"})

        await update.message.reply_text(
            text=get_template_price_mes,
            reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
        )

    if stage == "get_price":
        prompt_upd(table="templates", id=uniq_id, data={"price": float(message)})
        upd(table="users", user_id=user_id, data={"stage": "get_prompt"})

        await update.message.reply_text(
            text=get_prompt_mes,
            reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
        )
    
    if stage == "get_prompt":
        prompt_upd(table="templates", id=uniq_id, data={"prompt": message})
        upd(table="users", user_id=user_id, data={"stage": "start", "uniq_id": 0})
        template = prompt_get(table="templates", id=uniq_id)

        await update.message.reply_photo(
            photo=template["file_id"],
            caption=done_template_mes.format(
                template.get("name", "Yo'q"),
                template.get("price", 0),
                template.get("prompt", "yo'q")
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=ReplyKeyboardMarkup(start_but, resize_keyboard=True)
        )

    if stage == "edit_name":
        prompt_upd(table="templates", id=uniq_id, data={"name": message})
        template = prompt_get(table="templates", id=uniq_id)
        
        msg = await update.message.reply_photo(
            photo=template.get("file_id"),
            caption=template_mes.format(
                template.get("name"),
                template.get("price"),
                template.get("prompt"),
                template.get("created_at"),
                user.get("user_index")+1,
                len(prompt_get(table="templates"))
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(template_but)
        )
        upd(table="users", user_id=user_id, data={"stage": "templates", "uniq_id": 0})
        log_adder(type="caches", context=context, msg_id=update.message.message_id)
        await log_deletter(type="temp", user_id=user_id, context=context)
        log_adder(type="temp", context=context, msg_id=msg.message_id)
        
    if stage == "edit_price":
        prompt_upd(table="templates", id=uniq_id, data={"price": message})
        template = prompt_get(table="templates", id=int(uniq_id))

        msg = await update.message.reply_photo(
            photo=template.get("file_id"),
            caption=template_mes.format(
                template.get("name"),
                template.get("price"),
                template.get("prompt"),
                template.get("created_at"),
                user.get("user_index")+1,
                len(prompt_get(table="templates"))
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(template_but)
        )
        upd(table="users", user_id=user_id, data={"stage": "templates"})
        log_adder(type="caches", context=context, msg_id=update.message.message_id)
        await log_deletter(type="temp", user_id=user_id, context=context)
        log_adder(type="temp", context=context, msg_id=msg.message_id)

    if stage == "edit_prompt":
        prompt_upd(table="templates", id=uniq_id, data={"prompt": message})
        template = prompt_get(table="templates", id=uniq_id)

        msg = await update.message.reply_photo(
            photo=template.get("file_id"),
            caption=template_mes.format(
                template.get("name"),
                template.get("price"),
                template.get("prompt"),
                template.get("created_at"),
                user.get("user_index")+1,
                len(prompt_get(table="templates"))
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(template_but)
        )
        upd(table="users", user_id=user_id, data={"stage": "templates", "uniq_id": 0})
        log_adder(type="caches", context=context, msg_id=update.message.message_id)
        await log_deletter(type="temp", user_id=user_id, context=context)
        log_adder(type="temp", context=context, msg_id=msg.message_id)
    await log_deletter(type="caches", user_id=user_id, context=context)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user_id = q.from_user.id
    user = get(table="users", user_id=user_id)
    await q.answer()


    if "edit" in q.data:
        uniq_id = prompt_get(table="templates")[user.get("user_index")]["id"]

        if q.data == "edit_name":
            msg = await q.message.reply_text(
                text=get_template_name_mes,
                reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
            )
            upd(table="users", user_id=user_id, data={"stage": "edit_name","uniq_id": uniq_id})

        if q.data == "edit_price":
            msg = await q.message.reply_text(
                text=get_template_price_mes,
                reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
            )
            upd(table="users", user_id=user_id, data={"stage": "edit_price","uniq_id": uniq_id})
        if q.data == "edit_prompt":
            msg = await q.message.reply_text(
                text=get_prompt_mes,
                reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
            )
            upd(table="users", user_id=user_id, data={"stage": "edit_prompt","uniq_id": uniq_id})

    if "prev" in q.data or "next" in q.data:
        index = user.get("user_index")
        templates = prompt_get(table="templates")

        if q.data == "prev_template":
            if index > 0:
                index-=1
            else:
                index=len(templates)-1
        if q.data == "next_template":
            if index < len(templates)-1:
                index+=1
            else:
                index=0
        
        template = templates[index]

        await q.edit_message_media(
            media=InputMediaPhoto(
                media=template.get("file_id"),
                caption=template_mes.format(
                    template.get("name"),
                    template.get("price"),
                    template.get("prompt"),
                    template.get("created_at"),
                    index+1,
                    len(templates)
                ),
                parse_mode=ParseMode.HTML))
        
        await q.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(template_but)
        )
        await log_deletter(type="caches", user_id=user_id, context=context)
        upd(table="users", user_id=user_id, data={"user_index": index, "stage": "templates"})

    if q.data == "delete_template":
        uniq_id = prompt_get(table="templates")[user.get("user_index")]["id"]
        index = user.get("user_index")
        prompt_delete(table="templates", id=uniq_id)
        templates = prompt_get(table="templates")
        
        if len(templates) > 1:
            index-=1
        else:
            index=0
        try:
            template = templates[index]
            await q.edit_message_media(
                media=InputMediaPhoto(media=template.get("file_id"), caption=template_mes.format(
                    template.get("name"),
                    template.get("price"),
                    template.get("prompt"),
                    template.get("created_at"),
                    index+1,
                    len(templates)
                ),
                parse_mode=ParseMode.HTML))
            await q.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(template_but)
            )
        except:
            msg = await q.message.reply_text(
                text=main_menu_mes,
                reply_markup=ReplyKeyboardMarkup(start_but, resize_keyboard=True)
            )
            upd(table="users", user_id=user_id, data={"stage": "start"})
            await log_deletter(type="caches", user_id=user_id, context=context)
            await log_deletter(type="temp", user_id=user_id, context=context)

        upd(table="users", user_id=user_id, data={"user_index": index})

    if q.data == "add_template":
        msg = await q.message.reply_text(
            text=get_photo_mes,
            reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
        )
        upd(table="users", user_id=user_id, data={"stage": "get_photo"})

    if q.data == "back":
        upd(table="users", user_id=user_id, data={"stage": "start", "uniq_id": 0})

        msg = await q.message.reply_text(
            text=main_menu_mes,
            reply_markup=ReplyKeyboardMarkup(start_but, resize_keyboard=True)
        )
        await q.delete_message()
        await log_deletter(type="temp", user_id=user_id, context=context)
        await log_deletter(type="caches", user_id=user_id, context=context)

    try:
        await log_deletter(user_id=user_id, type="caches", context=context)
        log_adder(type="caches", msg_id=msg.message_id, context=context)
    except:
        pass

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user = get(table="users", user_id=user_id)
    stage = user.get("stage")
    file_id = update.message.photo[-1]['file_id']
    uniq_id = update.message.message_id


    if stage == "get_photo":
        prompt_insert(table="templates", data={
            "file_id": file_id,
            "name": None,
            "price": 0.0,
            "prompt": None,
            "author_id": user_id
        },id=uniq_id
        )

        upd(table="users", user_id=user_id, data={"stage": "get_name", "uniq_id": uniq_id})

        await update.message.reply_text(
            text=get_template_name_mes,
            reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
        )