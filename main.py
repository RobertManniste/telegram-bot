import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from database import create_tables
from registration import registration_handler
from premium import send_premium_invoice
from matching import matching_handlers, browse_profiles


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💙 Добро пожаловать в Europe Match\n\n"
        "Выберите вариант:"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Пробный период", callback_data="trial")],
        [InlineKeyboardButton("💎 Купить Premium", callback_data="premium")],
        [InlineKeyboardButton("👀 Смотреть анкеты", callback_data="browse")]
    ])

    await update.message.reply_text(text, reply_markup=keyboard)


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "trial":
        await context.bot.send_message(query.message.chat_id, "Введите /register")

    elif query.data == "premium":
        await send_premium_invoice(query, context)

    elif query.data == "browse":
        await browse_profiles(query, context)


def main():
    create_tables()

    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(registration_handler())

    for handler in matching_handlers():
        app.add_handler(handler)

    app.add_handler(CallbackQueryHandler(buttons, pattern="^(trial|premium|browse)$"))

    app.run_polling()


if __name__ == "__main__":
    main()
