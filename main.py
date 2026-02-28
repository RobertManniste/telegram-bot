import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters,
)

from database import create_tables
from registration import registration_handler
from premium import send_premium_invoice, successful_payment
from matching import matching_handlers, browse_profiles


# ================== ГЛАВНОЕ МЕНЮ ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💙 Добро пожаловать в Europe Match\n\n"
        "Мы объединяем людей по всей Европе для знакомств, общения "
        "и серьёзных отношений 🌍\n\n"
        "🎁 Пробный период 3 дня:\n"
        "• 20 сообщений в день\n"
        "• Частичный доступ к фото\n"
        "• Возможность начать общение\n\n"
        "💎 Premium открывает:\n"
        "• Неограниченные сообщения\n"
        "• Полный доступ ко всем фото\n"
        "• Приоритет профиля в поиске\n"
        "• Расширенные возможности общения\n\n"
        "Выберите вариант:"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Начать пробный период", callback_data="trial")],
        [InlineKeyboardButton("💎 Купить Premium (999⭐)", callback_data="premium")],
        [InlineKeyboardButton("👀 Смотреть анкеты", callback_data="browse")]
    ])

    await update.message.reply_text(text, reply_markup=keyboard)


# ================== КНОПКИ ==================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "trial":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Для регистрации введите /register"
        )

    elif query.data == "premium":
        await send_premium_invoice(query, context)

    elif query.data == "browse":
        await browse_profiles(query, context)


# ================== PRE-CHECKOUT ==================

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


# ================== MAIN ==================

def main():
    # создаём таблицы при запуске
    create_tables()

    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # --- Стартовое меню
    app.add_handler(CommandHandler("start", start))

    # --- Регистрация
    app.add_handler(registration_handler())

    # --- Matching (лайки + чат)
    for handler in matching_handlers():
        app.add_handler(handler)

    # --- Кнопки главного меню
    app.add_handler(CallbackQueryHandler(buttons, pattern="^(trial|premium|browse)$"))

    # --- Оплата
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    app.run_polling()


if __name__ == "__main__":
    main()
