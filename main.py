import os
import datetime
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
    PreCheckoutQueryHandler,
    MessageHandler,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

PREMIUM_PRICE = 999
TRIAL_DAYS = 3
TRIAL_MESSAGE_LIMIT = 5

# 🗂 Простая база пользователей
users = {}


# ---------------- HELPER ----------------

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "trial_start": datetime.datetime.now(),
            "is_premium": False,
            "daily_messages": 0,
            "last_message_date": datetime.date.today()
        }
    return users[user_id]


def is_trial_active(user):
    if user["is_premium"]:
        return False
    delta = datetime.datetime.now() - user["trial_start"]
    return delta.days < TRIAL_DAYS


# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = get_user(update.effective_user.id)

    keyboard = [
        [InlineKeyboardButton("📷 Смотреть фото", callback_data="photos")],
        [InlineKeyboardButton("💎 Купить Premium (999⭐)", callback_data="premium")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💙 Добро пожаловать в Europe Match\n\n"
        "🎁 Вам доступен пробный период 3 дня.\n\n"
        "🔒 В пробной версии:\n"
        f"• Лимит {TRIAL_MESSAGE_LIMIT} сообщений в день\n"
        "• Часть фото скрыта\n\n"
        "💎 Premium снимает все ограничения.",
        reply_markup=reply_markup
    )


# ---------------- PHOTOS ----------------

async def photos_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_data = get_user(query.from_user.id)

    if user_data["is_premium"]:
        await query.message.reply_photo(
            photo="https://via.placeholder.com/500",
            caption="🔥 Полное фото доступно (Premium)"
        )
    else:
        await query.message.reply_text(
            "🔒 Фото частично скрыто.\n\n"
            "Купите Premium для полного доступа 💎"
        )


# ---------------- PREMIUM BUY ----------------

async def premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    prices = [LabeledPrice("Premium подписка", PREMIUM_PRICE)]

    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title="💎 Premium доступ",
        description="Полный доступ без ограничений",
        payload="premium-access",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="XTR",
        prices=prices,
    )


# ---------------- PAYMENT ----------------

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = get_user(update.effective_user.id)
    user_data["is_premium"] = True

    await update.message.reply_text(
        "🎉 Поздравляем!\n\n"
        "💎 Premium активирован.\n"
        "Все ограничения сняты!"
    )


# ---------------- MESSAGE LIMIT ----------------

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = get_user(update.effective_user.id)

    if user_data["is_premium"]:
        return

    today = datetime.date.today()

    if user_data["last_message_date"] != today:
        user_data["daily_messages"] = 0
        user_data["last_message_date"] = today

    if not is_trial_active(user_data):
        await update.message.reply_text(
            "⛔ Пробный период завершён.\n\n"
            "Купите Premium для продолжения 💎"
        )
        return

    if user_data["daily_messages"] >= TRIAL_MESSAGE_LIMIT:
        await update.message.reply_text(
            "🚫 Вы достигли лимита сообщений на сегодня.\n\n"
            "💎 Premium снимает ограничения."
        )
        return

    user_data["daily_messages"] += 1


# ---------------- MAIN ----------------

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(photos_callback, pattern="photos"))
    app.add_handler(CallbackQueryHandler(premium_callback, pattern="premium"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
