from telegram import InlineKeyboardButton

start_but = [
    ["Rasm Yaratish🪄"],
    ["Shablon🔥", "Rasmlarim🗂"],
    ["Balans 💳","Sozlamalar⚙️"]
]

back_but = [
    ["Ortga🔙"]
]

photo_but = [
    [InlineKeyboardButton("Saqlash📁", callback_data="save"),InlineKeyboardButton("Ortga🔙", callback_data="back")]
]

saved_images_but = [
    [InlineKeyboardButton("⏮️", callback_data="prev_saved"), InlineKeyboardButton("⏭️", callback_data="next_saved")],
    [InlineKeyboardButton("O'chirish🗑", callback_data="delete"), InlineKeyboardButton("Ortga🔙", callback_data="back")]
]