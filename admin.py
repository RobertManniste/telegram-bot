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


def log_action(action):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO admin_logs (action) VALUES (%s)",
        (action,)
    )
    conn.commit()
    cur.close()
    conn.close()


# ================= MAIN PANEL =================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Пользователи", callback_data="users")],
        [InlineKeyboardButton("📷 Фото на проверке", callback_data="photos")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="broadcast")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
    ])

    await update.message.reply_text("⚙ ADMIN PANEL v4", reply_markup=keyboard)


# ================= USERS =================

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id, name FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()

    keyboard = []
    for u in users:
        keyboard.append([
            InlineKeyboardButton(
                f"{u[1]} ({u[0]})",
                callback_data=f"user_{u[0]}"
            )
        ])

    await query.message.reply_text(
        "Выберите пользователя:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, age, bio, premium_until, is_banned
        FROM users WHERE telegram_id=%s
    """, (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return

    name, age, bio, premium_until, banned = user

    text = f"""
👤 {name}
Возраст: {age}
Bio: {bio}
Premium до: {premium_until}
Забанен: {banned}
"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Premium", callback_data=f"prem_{user_id}")],
        [InlineKeyboardButton("🚫 Бан", callback_data=f"ban_{user_id}")],
        [InlineKeyboardButton("♻ Разбан", callback_data=f"unban_{user_id}")],
        [InlineKeyboardButton("💬 Переписки", callback_data=f"msgs_{user_id}")]
    ])

    await query.message.reply_text(text, reply_markup=keyboard)


# ================= PREMIUM =================

async def premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])
    context.user_data["target"] = user_id

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("7 дней", callback_data="dur_7")],
        [InlineKeyboardButton("30 дней", callback_data="dur_30")],
        [InlineKeyboardButton("180 дней", callback_data="dur_180")],
        [InlineKeyboardButton("365 дней", callback_data="dur_365")]
    ])

    await query.message.reply_text("Выберите срок:", reply_markup=keyboard)


async def set_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    days = int(query.data.split("_")[1])
    user_id = context.user_data.get("target")

    premium_until = datetime.utcnow() + timedelta(days=days)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET premium_until=%s WHERE telegram_id=%s",
        (premium_until, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    log_action(f"Premium {days} days to {user_id}")

    await query.message.reply_text(f"💎 Premium выдан на {days} дней")


# ================= BAN =================

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[1])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_banned=TRUE WHERE telegram_id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    log_action(f"Banned {user_id}")
    await query.message.reply_text("🚫 Пользователь забанен")


async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[1])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_banned=FALSE WHERE telegram_id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    log_action(f"Unbanned {user_id}")
    await query.message.reply_text("♻ Пользователь разбанен")


# ================= MESSAGES =================

async def view_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[1])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT sender_id, receiver_id, text
        FROM messages
        WHERE sender_id=%s OR receiver_id=%s
        ORDER BY sent_at DESC
        LIMIT 30
    """, (user_id, user_id))

    messages = cur.fetchall()
    cur.close()
    conn.close()

    if not messages:
        await query.message.reply_text("Сообщений нет")
        return

    text = ""
    for m in messages:
        text += f"{m[0]} ➜ {m[1]}: {m[2]}\n"

    await query.message.reply_text(text)


# ================= STATS =================

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE premium_until > NOW()")
    premium = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE is_banned=TRUE")
    banned = cur.fetchone()[0]

    cur.close()
    conn.close()

    await query.message.reply_text(
        f"👥 Пользователей: {total}\n💎 Premium: {premium}\n🚫 Бан: {banned}"
    )


def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),
        CallbackQueryHandler(list_users, pattern="^users$"),
        CallbackQueryHandler(user_profile, pattern="^user_"),
        CallbackQueryHandler(premium_menu, pattern="^prem_"),
        CallbackQueryHandler(set_premium, pattern="^dur_"),
        CallbackQueryHandler(ban_user, pattern="^ban_"),
        CallbackQueryHandler(unban_user, pattern="^unban_"),
        CallbackQueryHandler(view_messages, pattern="^msgs_"),
        CallbackQueryHandler(show_stats, pattern="^stats$")
    ]
