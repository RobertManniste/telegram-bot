import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from database import create_tables
from registration import start_registration
from premium import send_premium_invoice


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💙 Добро пожаловать в Europe Match\n\n"
        "Мы объединяем людей по всей Европе для знакомств, общения "
        "и серьёзных отношений.\n"
        "Найди свою вторую половинку быстро и безопасно 🌍\n\n"
        "🎁 Вам доступен пробный период 3 дня!\n\n"
        "В пробной версии:\n"
        "• 20 сообщений в день\n"
        "• Частичный доступ к фотографиям\n"
        "• Возможность начать общение\n\n"
        "💎 Premium открывает:\n"
        "• Неограниченные сообщения\n"
        "• Полный доступ ко всем фото\n"
        "• Приоритет профиля в поиске\n"
        "• Расширенные возможности общения\n\n"
        "Открой больше возможностей ❤️"
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
        await start_registration(query, context, trial=True)

    elif query.data == "premium":
        await send_premium_invoice(query, context)


def main():
    create_tables()

    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    app.run_polling()


if __name__ == "__main__":
    main()
