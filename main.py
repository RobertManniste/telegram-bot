import os
import sqlite3
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    LabeledPrice
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    filters,
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_NAME = "lovia.db"


# ================= DATABASE =================

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            name TEXT,
            age TEXT,
            city TEXT,
            premium INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def get_user(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()

    conn.close()
    return user


def add_user(telegram_id, name, age, city):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (telegram_id, name, age, city)
        VALUES (?, ?, ?, ?)
    """, (telegram_id, name, age, city))

    conn.commit()
    conn.close()


def activate_premium(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET premium = 1 WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()


# ================= MENUS =================

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


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user = get_user(telegram_id)

    if user:
        await update.message.reply_text(
            "❤️ Добро пожаловать в Lovia",
            reply_markup=registered_menu()
        )
    else:
        await update.message.reply_text(
            """❤️ Lovia — знакомства без границ

Создай профиль и начни знакомства уже сейчас 💫""",
            reply_markup=new_user_menu()
        )


# ================= REGISTRATION =================

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
        name = context.user_data["name"]
        age = context.user_data["age"]
        city = update.message.text

        add_user(update.effective_user.id, name, age, city)

        await update.message.reply_text(
            "Регистрация завершена ❤️",
            reply_markup=registered_menu()
        )

        context.user_data.clear()


# ================= VIEW PROFILES =================

async def view_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👀 Здесь будут анкеты (дальше добавим свайпы)",
        reply_markup=registered_menu()
    )


# ================= PREMIUM =================

async def buy_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = [LabeledPrice("Lovia Premium", 349)]

    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title="Lovia Premium",
        description="Безлимитный доступ ко всем функциям",
        payload="premium",
        provider_token="",  # для Telegram Stars оставляем пустым
        currency="XTR",
        prices=prices,
    )


async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    activate_premium(update.effective_user.id)

    await update.message.reply_text(
        "💎 Premium активирован!",
        reply_markup=registered_menu()
    )


# ================= MAIN =================

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