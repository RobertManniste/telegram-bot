import os
import psycopg2
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

ADMIN_ID = int(os.getenv("ADMIN_ID"))


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def is_admin(user_id):
    return user_id == ADMIN_ID


# ================== ПАНЕЛЬ ==================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Нет доступа")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("💎 Premium", callback_data="admin_premium")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")]
    ])

    await update.message.reply_text("⚙ Админ панель", reply_markup=keyboard)


# ================== PREMIUM ==================

async def premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("7 дней", callback_data="prem_7")],
        [InlineKeyboardButton("30 дней", callback_data="prem_30")],
        [InlineKeyboardButton("6 месяцев", callback_data="prem_180")],
        [InlineKeyboardButton("1 год", callback_data="prem_365")]
    ])

    await query.message.reply_text("Выберите срок Premium:", reply_markup=keyboard)


async def select_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    days = int(query.data.split("_")[1])

    context.user_data["premium_days"] = days
    context.user_data["mode"] = "give_premium"

    await query.message.reply_text("Введите ID пользователя:")


async def process_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    mode = context.user_data.get("mode")

    if mode == "give_premium":
        try:
            user_id = int(update.message.text)
            days = context.user_data["premium_days"]

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

            await update.message.reply_text(
                f"💎 Premium выдан на {days} дней"
            )

        except:
            await update.message.reply_text("Ошибка ID")

        context.user_data.clear()


# ================== СТАТИСТИКА ==================

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
        f"📊 Пользователей: {total}\nАктивных Premium: {premium}"
    )


# ================== USERS ==================

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT telegram_id, name, premium_until FROM users")
    users = cur.fetchall()

    cur.close()
    conn.close()

    text = "👥 Пользователи:\n\n"

    for user in users:
        text += f"ID: {user[0]} | {user[1]} | Premium until: {user[2]}\n"

    await query.message.reply_text(text)


# ================== HANDLERS ==================

def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),
        CallbackQueryHandler(premium_menu, pattern="admin_premium"),
        CallbackQueryHandler(select_duration, pattern="prem_"),
        CallbackQueryHandler(show_stats, pattern="admin_stats"),
        CallbackQueryHandler(list_users, pattern="admin_users"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, process_admin),
    ]
