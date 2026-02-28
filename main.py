import os
from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice,
    Update
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from database import create_tables, activate_premium, get_connection
from registration import registration_handler, start_registration
from matching import matching_handlers
from admin import admin_handlers


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# ================= ПРОВЕРКА РЕГИСТРАЦИИ =================

def user_exists(telegram_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE telegram_id = %s", (telegram_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
💙 Europe Match — знакомства без границ

Ищешь любовь, общение или новые знакомства по Европе? 🌍  
Ты в правильном месте.

━━━━━━━━━━━━━━━
✨ Пробный доступ — 3 дня

В пробной версии:
• 20 сообщений в день
• Частичный доступ к фотографиям
• Возможность начать общение

━━━━━━━━━━━━━━━
💎 Premium

• Безлимитные сообщения
• Полный доступ ко всем фото
• Приоритет в поиске
• Неограниченные лайки

━━━━━━━━━━━━━━━
📌 Правила

• Уважайте других
• Никакого спама
• Никаких денежных запросов
• Запрещён откровенный и незаконный контент

Мы за безопасные знакомства ❤️
"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Начать заполнять анкету", callback_data="start_reg")],
        [InlineKeyboardButton("💎 Купить Premium", callback_data="buy_premium")]
    ])

    await update.message.reply_text(text, reply_markup=keyboard)


# ================= КНОПКА РЕГИСТРАЦИИ =================

async def handle_start_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id

    if user_exists(telegram_id):
        await query.message.reply_text("Вы уже зарегистрированы ✅")
        return

    # запускаем ConversationHandler регистрации
    await start_registration(update, context)


# ================= BUY PREMIUM =================

async def buy_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    prices = [LabeledPrice("Premium (1 месяц)", 399)]

    await context.bot.send_invoice(
        chat_id=query.from_user.id,
        title="Europe Match Premium",
        description="Безлимитные сообщения и полный доступ ко всем функциям.",
        payload="premium-month",
        provider_token="",
        currency="XTR",
        prices=prices,
    )


# ================= PRECHECKOUT =================

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)


# ================= УСПЕШНАЯ ОПЛАТА =================

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    activate_premium(user_id, 30)

    await update.message.reply_text(
        "🎉 Оплата прошла успешно!\n\nPremium активирован на 1 месяц 💎"
    )


# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    create_tables()

    # старт
    app.add_handler(CommandHandler("start", start))

    # кнопки
    app.add_handler(CallbackQueryHandler(handle_start_reg, pattern="start_reg"))
    app.add_handler(CallbackQueryHandler(buy_premium, pattern="buy_premium"))

    # оплата
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # регистрация (ConversationHandler)
    app.add_handler(registration_handler())

    # матчинг
    for h in matching_handlers():
        app.add_handler(h)

    # админка
    for h in admin_handlers():
        app.add_handler(h)

    app.run_polling()


if __name__ == "__main__":
    main()
