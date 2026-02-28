import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)

from database import create_tables
from registration import registration_handler
from matching import matching_handlers
from admin import admin_handlers

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# ================= START =================

async def start(update, context):
    text = """
💙 Europe Match — знакомства без границ

Ищете любовь, общение или новые знакомства по Европе? 🌍  
Здесь люди находят друг друга быстро и безопасно.

✨ Пробный доступ на 3 дня уже активирован.

📌 Важно:
• Уважайте других
• Никакого спама
• Никаких денежных запросов

Мы за безопасные знакомства ❤️
"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Начать заполнять анкету", callback_data="start_reg")],
        [InlineKeyboardButton("💎 Купить Premium — 399 ⭐", callback_data="buy_premium")]
    ])

    await update.message.reply_text(text, reply_markup=keyboard)


# ================= CALLBACKS =================

async def start_registration_callback(update, context):
    query = update.callback_query
    await query.answer()
    await query.message.delete()

    # запускаем регистрацию
    return await registration_handler().entry_points[0].callback(update, context)


async def buy_premium(update, context):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "💎 Premium — 399 ⭐\n\n"
        "✔ Безлимитные сообщения\n"
        "✔ Полный доступ ко всем фото\n"
        "✔ Приоритет в поиске\n\n"
        "Оплата скоро будет подключена."
    )


# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    create_tables()

    # start
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start_registration_callback, pattern="start_reg"))
    app.add_handler(CallbackQueryHandler(buy_premium, pattern="buy_premium"))

    # registration
    app.add_handler(registration_handler())

    # matching
    for h in matching_handlers():
        app.add_handler(h)

    # admin
    for h in admin_handlers():
        app.add_handler(h)

    app.run_polling()


if __name__ == "__main__":
    main()
