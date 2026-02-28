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

from database import create_tables, activate_premium
from registration import registration_handler
from matching import matching_handlers
from admin import admin_handlers

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
💙 Europe Match — знакомства без границ

Ищешь любовь, общение или новые знакомства по Европе? 🌍  
Ты в правильном месте.

Здесь ты можешь:
• Смотреть анкеты
• Получать сообщения
• Общаться после совпадения

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


# ================= BUY PREMIUM (Telegram Stars) =================

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


# ================= SUCCESSFUL PAYMENT =================

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    activate_premium(user_id, days=30)

    await update.message.reply_text(
        "🎉 Оплата прошла успешно!\n\n"
        "Premium активирован на 1 месяц 💎"
    )


# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    create_tables()

    # --- БАЗОВЫЕ ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buy_premium, pattern="^buy_premium$"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # ======================================================
    # 🔥 СНАЧАЛА АДМИН (ВАЖНО!)
    # ======================================================
    for handler in admin_handlers():
        app.add_handler(handler)

    # ======================================================
    # ПОТОМ РЕГИСТРАЦИЯ
    # ======================================================
    app.add_handler(registration_handler())

    # ======================================================
    # ПОТОМ МАТЧИНГ
    # ======================================================
    for handler in matching_handlers():
        app.add_handler(handler)

    app.run_polling()


if __name__ == "__main__":
    main()
