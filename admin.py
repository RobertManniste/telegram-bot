import os
from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from database import get_connection, activate_premium

ADMIN_ID = int(os.getenv("ADMIN_ID"))


# ================= CHECK ADMIN =================

def is_admin(user_id):
    return user_id == ADMIN_ID


# ================= ADMIN PANEL =================

async def admin_panel(update, context):
    if not is_admin(update.effective_user.id):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📨 Рассылка", callback_data="admin_broadcast")]
    ])

    await update.message.reply_text("⚙ Админ панель v7", reply_markup=keyboard)


# ================= USERS =================

async def show_users(update, context):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id, name FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()

    buttons = []
    for u in users:
        buttons.append([
            InlineKeyboardButton(
                f"{u[1]} ({u[0]})",
                callback_data=f"view_{u[0]}"
            )
        ])

    await query.message.reply_text(
        "👥 Пользователи:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def view_user(update, context):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, age, city, bio, premium_until, is_banned
        FROM users WHERE telegram_id = %s
    """, (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        await query.message.reply_text("Пользователь не найден.")
        return

    premium = "Да" if user[4] and user[4] > datetime.now() else "Нет"
    banned = "Да" if user[5] else "Нет"

    text = f"""
Имя: {user[0]}
Возраст: {user[1]}
Город: {user[2]}
Bio: {user[3]}

Premium: {premium}
Бан: {banned}
"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💎 30 дней Premium", callback_data=f"giveprem_{user_id}")
        ],
        [
            InlineKeyboardButton("🚫 Бан", callback_data=f"ban_{user_id}"),
            InlineKeyboardButton("✅ Разбан", callback_data=f"unban_{user_id}")
        ]
    ])

    await query.message.reply_text(text, reply_markup=keyboard)


# ================= PREMIUM =================

async def give_premium(update, context):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])
    activate_premium(user_id, 30)

    await query.message.reply_text("✅ Premium выдан на 30 дней.")


# ================= BAN =================

async def ban_user(update, context):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_banned = TRUE WHERE telegram_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    await query.message.reply_text("🚫 Пользователь забанен.")


async def unban_user(update, context):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_banned = FALSE WHERE telegram_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    await query.message.reply_text("✅ Пользователь разбанен.")


# ================= STATS =================

async def show_stats(update, context):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE premium_until > NOW()")
    premium_users = cur.fetchone()[0]

    cur.close()
    conn.close()

    text = f"""
📊 Статистика

Пользователи: {total_users}
Активный Premium: {premium_users}
"""

    await query.message.reply_text(text)


# ================= BROADCAST =================

async def start_broadcast(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["broadcast_mode"] = True
    await query.message.reply_text("Введите текст рассылки:")


async def send_broadcast(update, context):
    if not context.user_data.get("broadcast_mode"):
        return

    text = update.message.text

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()

    for u in users:
        try:
            await context.bot.send_message(u[0], text)
        except:
            pass

    context.user_data["broadcast_mode"] = False
    await update.message.reply_text("✅ Рассылка завершена.")


# ================= HANDLERS =================

def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),

        CallbackQueryHandler(show_users, pattern="^admin_users$"),
        CallbackQueryHandler(show_stats, pattern="^admin_stats$"),
        CallbackQueryHandler(start_broadcast, pattern="^admin_broadcast$"),

        CallbackQueryHandler(view_user, pattern="^view_"),
        CallbackQueryHandler(give_premium, pattern="^giveprem_"),
        CallbackQueryHandler(ban_user, pattern="^ban_"),
        CallbackQueryHandler(unban_user, pattern="^unban_"),

        MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast),
    ]
