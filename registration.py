import os
import psycopg2
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    filters
)

# Состояния
AGE_CONFIRM, NAME, AGE, CITY, GENDER, LOOKING, PHOTO, BIO = range(8)


# Подключение к БД
def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def user_exists(telegram_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE telegram_id = %s", (telegram_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None


# Старт регистрации
async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    if user_exists(telegram_id):
        await update.message.reply_text("Вы уже зарегистрированы ✅")
        return ConversationHandler.END

    keyboard = [
        ["✅ Мне есть 18 лет"],
        ["❌ Мне нет 18"]
    ]

    await update.message.reply_text(
        "🔞 Сервис доступен только для лиц 18+.\nПодтвердите возраст:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return AGE_CONFIRM


# Подтверждение 18+
async def confirm_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "нет" in update.message.text.lower():
        await update.message.reply_text(
            "⛔ Доступ запрещён. Сервис доступен только 18+.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Введите ваше имя:",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME


# Имя
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Сколько вам лет?")
    return AGE


# Возраст
async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("Введите возраст числом.")
        return AGE

    age = int(update.message.text)

    if age < 18:
        await update.message.reply_text("⛔ Регистрация возможна только с 18 лет.")
        return ConversationHandler.END

    context.user_data["age"] = age
    await update.message.reply_text("Ваш город?")
    return CITY


# Город
async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text

    keyboard = [["Мужчина", "Женщина"]]
    await update.message.reply_text(
        "Ваш пол?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return GENDER


# Пол
async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = update.message.text

    keyboard = [["Мужчин", "Женщин"]]
    await update.message.reply_text(
        "Кого вы ищете?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return LOOKING


# Кого ищет
async def get_looking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["looking_for"] = update.message.text
    await update.message.reply_text("Отправьте ваше фото:")
    return PHOTO


# Фото
async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Пожалуйста, отправьте фото.")
        return PHOTO

    context.user_data["photo"] = update.message.photo[-1].file_id
    await update.message.reply_text("Напишите немного о себе:")
    return BIO


# Описание и сохранение
async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bio"] = update.message.text

    telegram_id = update.effective_user.id
    trial_end = datetime.now() + timedelta(days=3)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users 
        (telegram_id, name, age, city, bio, photo, gender, looking_for, trial_end)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        telegram_id,
        context.user_data["name"],
        context.user_data["age"],
        context.user_data["city"],
        context.user_data["bio"],
        context.user_data["photo"],
        context.user_data["gender"],
        context.user_data["looking_for"],
        trial_end
    ))

    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text("🎉 Регистрация завершена! Вам доступно 3 дня пробного периода.")

    return ConversationHandler.END


# Хендлер
def registration_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("register", start_registration)],
        states={
            AGE_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_age)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            LOOKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_looking)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
        },
        fallbacks=[]
    )
