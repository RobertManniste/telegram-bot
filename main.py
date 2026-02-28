import os
from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
)

from database import create_tables, activate_premium
from registration import registration_handler
from matching import matching_handlers
from admin import admin_handlers

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")


# ================= START =================

async def start(update, context):

    text = """
💙 Europe Match — знакомства без границ

Ищешь любовь, общение или новые знакомства по Европе? 🌍  
Ты в правильном месте.

Здесь ты можешь:
• Смотреть анкеты
• Получать взаимные симпатии
• Общаться после совпадения

✨ Пробный доступ — 3 дня

В пробной версии:
• 20 сообщений в день
• Частичный доступ к фотографиям
• Возможность начать общение

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


# ================= BUY PREMIUM =================

async def buy_premium(update, context):
    query = update.callback_query
    await query.answer()

    prices = [LabeledPrice("Premium подписка (1 месяц)", 399)]

    await context.bot.send_invoice(
        chat_id=query.from_user.id,
        title="Europe Match Premium",
        description="Безлимитные сообщения и полный доступ ко всем функциям.",
        payload="premium-month",
        provider_token=PROVIDER_TOKEN,
        currency="XTR",
        prices=prices,
    )


# ================= PRECHECKOUT =================

async def precheckout_callback(update, context):
    query = update.pre_checkout_query
    await query.answer(ok=True)


# ================= SUCCESSFUL PAYMENT =================

async def successful_payment(update, context):
    user_id = update.message.from_user.id

    activate_premium(user_id, days=30)

    await update.message.reply_text(
        "🎉 Оплата прошла успешно!\n\n"
        "Premium активирован на 1 месяц.\n"
        "Наслаждайтесь всеми возможностями 💎"
    )


# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    create_tables()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buy_premium, pattern="buy_premium"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))

    app.add_handler(registration_handler())

    for h in matching_handlers():
        app.add_handler(h)

    for h in admin_handlers():
        app.add_handler(h)

    app.add_handler(CommandHandler("successful_payment", successful_payment))

    app.run_polling()


if __name__ == "__main__":
    main()
