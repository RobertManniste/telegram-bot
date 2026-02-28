import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    PreCheckoutQueryHandler
)

TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

PRICE = 400  # 400 Telegram Stars


# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    welcome_text = (
        "💙 Добро пожаловать в Europe Match\n\n"
        "Ищешь серьёзные отношения или новые знакомства по всей Европе?\n"
        "Ты в правильном месте.\n\n"
        "🌍 Мы объединяем людей без границ.\n"
        "🔐 Открывай фото профиля и начинай общение уже сегодня.\n\n"
        "📌 Правила платформы:\n"
        "1️⃣ Уважение к каждому пользователю\n"
        "2️⃣ Без спама и мошенничества\n"
        "3️⃣ Запрещён откровенный контент\n"
        "4️⃣ Не запрашивать деньги и личные данные\n\n"
        "Нажимая кнопки ниже, вы соглашаетесь с правилами."
    )

    keyboard = [
        [InlineKeyboardButton("🔓 Открыть фото", callback_data="buy")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup
    )


# ---------------- RULES BUTTON ----------------

async def rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "📜 Правила Europe Match:\n\n"
        "• Уважительное общение\n"
        "• Запрещён спам и мошенничество\n"
        "• Никакого запрещённого контента\n"
        "• Не переводите деньги незнакомым людям\n\n"
        "Нарушение правил = блокировка 🚫"
    )


# ---------------- BUY BUTTON ----------------

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    prices = [LabeledPrice("Доступ к оригинальному фото", PRICE)]

    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title="🔓 Открыть фото",
        description="Доступ к оригинальному фото профиля",
        payload="photo-access",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="XTR",  # Telegram Stars
        prices=prices,
    )


# ---------------- PAYMENT HANDLERS ----------------

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Оплата прошла успешно!\n\n"
        "Вот ваше оригинальное фото 👇"
    )

    # 👉 ВСТАВЬ СЮДА СВОЮ ФОТОГРАФИЮ
    await update.message.reply_photo(
        photo="https://via.placeholder.com/500"
    )


# ---------------- MAIN ----------------

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(rules_callback, pattern="rules"))
    app.add_handler(CallbackQueryHandler(buy_callback, pattern="buy"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(CommandHandler("successful_payment", successful_payment_callback))

    app.run_polling()


if __name__ == "__main__":
    main()
