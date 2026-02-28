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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💙 Добро пожаловать в Europe Match\n\n"
        "Мы объединяем людей по всей Европе для знакомств и серьёзных отношений 🌍\n\n"
        "🎁 Пробный период 3 дня:\n"
        "• 20 сообщений в день\n"
        "• Частичный доступ к фото\n\n"
        "💎 Premium:\n"
        "• Безлимитные сообщения\n"
        "• Полный доступ ко всем фото\n"
        "• Приоритет в поиске\n\n"
        "Выберите вариант:"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Начать пробный период", callback_data="trial")],
        [InlineKeyboardButton("💎 Купить Premium (999⭐)", callback_data="premium")]
    ])

    await update.message.reply_text(text, reply_markup=keyboard)


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "trial":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Начинаем регистрацию 👇"
        )
        return await registration_handler().entry_points[0].callback(update, context)

    elif query.data == "premium":
        await send_premium_invoice(query, context)


def main():
    create_tables()

    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(registration_handler())

    app.run_polling()


if __name__ == "__main__":
    main()
