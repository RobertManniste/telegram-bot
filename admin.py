import os
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler
)

from database import (
    get_connection,
    activate_premium,
    remove_premium,
    ban_user,
    unban_user,
    approve_photo,
    delete_photo
)

ADMIN_ID = int(os.getenv("ADMIN_ID"))


def is_admin(user_id):
    return user_id == ADMIN_ID


# ================= MAIN PANEL =================

async def admin_panel(update, context):
    if not is_admin(update.effective_user.id):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Пользователи", callback_data="users")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
    ])

    await update.message.reply_text("⚙ Админ панель", reply_markup=keyboard)


# ================= USERS LIST =================

async def show_users(update, context):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id, name FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()

    buttons = [
        [InlineKeyboardButton(f"{u[1]} ({u[0]})", callback_data=f"user_{u[0]}")]
        for u in users
    ]

    await query.message.reply_text(
        "👥 Пользователи:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ================= USER CONTROL =================

async def user_control(update, context):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])
    context.user_data["target_user"] = user_id

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Premium 30 дней", callback_data="prem30")],
        [InlineKeyboardButton("❌ Снять Premium", callback_data="remove_prem")],
        [InlineKeyboardButton("🚫 Бан", callback_data="ban")],
        [InlineKeyboardButton("✅ Разбан", callback_data="unban")],
        [InlineKeyboardButton("🖼 Одобрить фото", callback_data="approve_photo")],
        [InlineKeyboardButton("🗑 Удалить фото", callback_data="delete_photo")]
    ])

    await query.message.reply_text(
        f"Управление пользователем {user_id}",
        reply_markup=keyboard
    )


# ================= ACTIONS =================

async def give_premium(update, context):
    query = update.callback_query
    await query.answer()

    user_id = context.user_data.get("target_user")
    activate_premium(user_id, 30)

    await query.message.reply_text("✅ Premium выдан на 30 дней.")


async def remove_prem(update, context):
    query = update.callback_query
    await query.answer()

    user_id = context.user_data.get("target_user")
    remove_premium(user_id)

    await query.message.reply_text("❌ Premium снят.")


async def ban(update, context):
    query = update.callback_query
    await query.answer()

    user_id = context.user_data.get("target_user")
    ban_user(user_id)

    await query.message.reply_text("🚫 Пользователь забанен.")


async def unban(update, context):
    query = update.callback_query
    await query.answer()

    user_id = context.user_data.get("target_user")
    unban_user(user_id)

    await query.message.reply_text("✅ Пользователь разбанен.")


async def approve(update, context):
    query = update.callback_query
    await query.answer()

    user_id = context.user_data.get("target_user")
    approve_photo(user_id)

    await query.message.reply_text("🖼 Фото одобрено.")


async def delete(update, context):
    query = update.callback_query
    await query.answer()

    user_id = context.user_data.get("target_user")
    delete_photo(user_id)

    await query.message.reply_text("🗑 Фото удалено.")


# ================= STATS =================

async def show_stats(update, context):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM messages")
    messages = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE premium_until > NOW()")
    premium = cur.fetchone()[0]

    cur.close()
    conn.close()

    text = f"""
📊 Статистика

Пользователи: {users}
Сообщения: {messages}
Активный Premium: {premium}
"""

    await query.message.reply_text(text)


# ================= HANDLERS =================

def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),
        CallbackQueryHandler(show_users, pattern="users"),
        CallbackQueryHandler(user_control, pattern="user_"),
        CallbackQueryHandler(give_premium, pattern="prem30"),
        CallbackQueryHandler(remove_prem, pattern="remove_prem"),
        CallbackQueryHandler(ban, pattern="ban"),
        CallbackQueryHandler(unban, pattern="unban"),
        CallbackQueryHandler(approve, pattern="approve_photo"),
        CallbackQueryHandler(delete, pattern="delete_photo"),
        CallbackQueryHandler(show_stats, pattern="stats"),
    ]
