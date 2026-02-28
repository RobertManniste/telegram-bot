import os
import psycopg2
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

ADMIN_ID = int(os.getenv("ADMIN_ID"))


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def is_admin(user_id):
    return user_id == ADMIN_ID


# =========================
# ГЛАВНАЯ ПАНЕЛЬ
# =========================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Нет доступа")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("📷 Фото на проверке", callback_data="admin_photos")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")]
    ])

    await update.message.reply_text("⚙ Админ панель", reply_markup=keyboard)


# =========================
# СПИСОК ПОЛЬЗОВАТЕЛЕЙ
# =========================

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT telegram_id, name FROM users")
    users = cur.fetchall()

    cur.close()
    conn.close()

    if not users:
        await query.message.reply_text("Нет пользователей")
        return

    keyboard = []
    for user in users:
        keyboard.append([
            InlineKeyboardButton(
                f"{user[1]} ({user[0]})",
                callback_data=f"user_{user[0]}"
            )
        ])

    await query.message.reply_text(
        "Выберите пользователя:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# =========================

async def user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, age, bio, premium_until
        FROM users WHERE telegram_id=%s
    """, (user_id,))

    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        await query.message.reply_text("Пользователь не найден")
        return

    name, age, bio, premium_until = user

    text = f"""
👤 {name}
Возраст: {age}
Bio: {bio}
Premium до: {premium_until}
"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Выдать Premium", callback_data=f"giveprem_{user_id}")],
        [InlineKeyboardButton("💬 Посмотреть переписки", callback_data=f"msgs_{user_id}")]
    ])

    await query.message.reply_text(text, reply_markup=keyboard)


# =========================
# ВЫДАЧА PREMIUM
# =========================

async def give_premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])
    context.user_data["target_user"] = user_id

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("7 дней", callback_data="dur_7")],
        [InlineKeyboardButton("30 дней", callback_data="dur_30")],
        [InlineKeyboardButton("6 месяцев", callback_data="dur_180")],
        [InlineKeyboardButton("1 год", callback_data="dur_365")]
    ])

    await query.message.reply_text("Выберите срок:", reply_markup=keyboard)


async def set_premium_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    days = int(query.data.split("_")[1])
    user_id = context.user_data.get("target_user")

    premium_until = datetime.utcnow() + timedelta(days=days)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET premium_until=%s
        WHERE telegram_id=%s
    """, (premium_until, user_id))

    conn.commit()
    cur.close()
    conn.close()

    await query.message.reply_text(
        f"💎 Premium выдан на {days} дней"
    )


# =========================
# ПРОСМОТР СООБЩЕНИЙ
# =========================

async def view_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT sender_id, receiver_id, text, sent_at
        FROM messages
        WHERE sender_id=%s OR receiver_id=%s
        ORDER BY sent_at DESC
        LIMIT 20
    """, (user_id, user_id))

    messages = cur.fetchall()

    cur.close()
    conn.close()

    if not messages:
        await query.message.reply_text("Сообщений нет")
        return

    text = "Последние 20 сообщений:\n\n"

    for msg in messages:
        text += f"{msg[0]} ➜ {msg[1]}: {msg[2]}\n"

    await query.message.reply_text(text)


# =========================
# СТАТИСТИКА
# =========================

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM users
        WHERE premium_until IS NOT NULL
        AND premium_until > NOW()
    """)
    premium = cur.fetchone()[0]

    cur.close()
    conn.close()

    await query.message.reply_text(
        f"Пользователей: {total}\nPremium активных: {premium}"
    )


# =========================
# HANDLERS
# =========================

def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),
        CallbackQueryHandler(list_users, pattern="admin_users"),
        CallbackQueryHandler(user_profile, pattern="^user_"),
        CallbackQueryHandler(give_premium_menu, pattern="^giveprem_"),
        CallbackQueryHandler(set_premium_duration, pattern="^dur_"),
        CallbackQueryHandler(view_messages, pattern="^msgs_"),
        CallbackQueryHandler(show_stats, pattern="admin_stats"),
    ]
