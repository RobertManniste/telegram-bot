import os
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    filters,
)

from database import create_tables, get_user, add_user
from matching import show_next_profile

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ================== КНОПКИ ==================

def registered_menu():
    keyboard = [
        [KeyboardButton("👀 Смотреть анкеты")],
        [KeyboardButton("💎 Купить Premium")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def new_user_menu():
    keyboard = [
        [KeyboardButton("🚀 Начать заполнять анкету")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================== /start ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user = get_user(telegram_id)

    if user:
        await update.message.reply_text(
            "Добро пожаловать в Lovia ❤️",
            reply_markup=registered_menu()
        )
    else:
        await update.message.reply_text(
            """❤️ Lovia — знакомства без границ

Создай профиль и начни знакомства уже сейчас 💫""",
            reply_markup=new_user_menu()
        )

# ================== РЕГИСТРАЦИЯ ==================

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Как тебя зовут?")
    context.user_data["step"] = "name"

async def registration_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")

    if step == "name":
        context.user_data["name"] = update.message.text
        await update.message.reply_text("Сколько тебе лет?")
        context.user_data["step"] = "age"

    elif step == "age":
        context.user_data["age"] = update.message.text
        await update.message.reply_text("Из какого ты города?")
        context.user_data["step"] = "city"

    elif step == "city":
        name = context.user_data.get("name")
        age = context.user_data.get("age")
        city = update.message.text

        add_user(
            telegram_id=update.effective_user.id,
            name=name,
            age=age,
            city=city
        )

        await update.message.reply_text(
            "Регистрация завершена ❤️\nТеперь можешь смотреть анкеты!",
            reply_markup=registered_menu()
        )

        context.user_data.clear()

# ================== ПРОСМОТР АНКЕТ ==================

async def view_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_next_profile(update, context)

# ================== PREMIUM 349 ⭐ ==================

async def buy_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = [LabeledPrice("Premium Lovia", 349)]

    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title="Lovia Premium",
        description="Безлимитный доступ ко всем функциям",
        payload="premium_payment",
        provider_token="",  # для Telegram Stars оставить пустым
        currency="XTR",
        prices=prices,
    )

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💎 Premium активирован! Спасибо ❤️")

# ================== MAIN ==================

def main():
    create_tables()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("🚀 Начать заполнять анкету"),
        start_registration
    ))

    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("👀 Смотреть анкеты"),
        view_profiles
    ))

    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("💎 Купить Premium"),
        buy_premium
    ))

    app.add_handler(MessageHandler(filters.TEXT, registration_flow))

    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    app.run_polling()

if __name__ == "__main__":
    main()
