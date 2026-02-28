import os
import psycopg2
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes


ADMIN_ID = int(os.getenv("ADMIN_ID"))


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


# ================== ПРОВЕРКА АДМИНА ==================

def is_admin(user_id):
    return user_id == ADMIN_ID


# ================== ГЛАВНОЕ МЕНЮ ==================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("💎 Premium", callback_data="admin_premium")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")]
    ])

    await update.message.reply_text("⚙ Админ панель", reply_markup=keyboard)


# ================== СТАТИСТИКА ==================

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE premium=TRUE")
    premium_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM likes")
    total_likes = cur.fetchone()[0]

    cur.close()
    conn.close()

    await query.message.reply_text(
        f"📊 Статистика:\n\n"
        f"Всего пользователей: {total_users}\n"
        f"Premium: {premium_users}\n"
        f"Лайков: {total_likes}"
    )


# ================== СПИСОК ПОЛЬЗОВАТЕЛЕЙ ==================

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT telegram_id, name, premium FROM users LIMIT 20")
    users = cur.fetchall()

    cur.close()
    conn.close()

    text = "👥 Пользователи:\n\n"

    for user in users:
        text += f"ID: {user[0]} | {user[1]} | Premium: {user[2]}\n"

    await query.message.reply_text(text)


# ================== HANDLERS ==================

def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),
        CallbackQueryHandler(show_stats, pattern="admin_stats"),
        CallbackQueryHandler(list_users, pattern="admin_users")
    ]
