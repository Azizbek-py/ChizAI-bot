from telegram import InlineKeyboardButton

start_but = [
    ["Shablonlar🗂"],
    ["Balans💸"]
]

back_but = [["Ortga🔙"]]

template_but = [
    [InlineKeyboardButton("Nom✏️", callback_data="edit_name")],
    [InlineKeyboardButton("Narxi✏️", callback_data="edit_price")],
    [InlineKeyboardButton("Prompt✏️", callback_data="edit_prompt")],
    [InlineKeyboardButton("Template ADD➕", callback_data="add_template")],
    [InlineKeyboardButton("O'chirish🗑", callback_data="delete_template"), InlineKeyboardButton("Ortga🔙", callback_data="back")],
    [InlineKeyboardButton("⏮️", callback_data="prev_template"), InlineKeyboardButton("⏭️", callback_data="next_template")]

]

no_template_but = [
    ["Qo'shish➕"],
    ["Ortga🔙"]
]