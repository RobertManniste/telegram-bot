import os
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
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


# ================= ГЛАВНОЕ МЕНЮ =================

async def admin_panel(update, context):
    if not is_admin(update.effective_user.id):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("🖼 Модерация фото", callback_data="admin_photos")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📨 Рассылка", callback_data="admin_broadcast")]
    ])

    await update.message.reply_text("⚙ Админ панель v5", reply_markup=keyboard)


# ================= СПИСОК ПОЛЬЗОВАТЕЛЕЙ =================

async def show_users(update, context):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id, name FROM users ORDER BY id DESC")
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


# ================= ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ =================

async def user_profile(update, context):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])
    context.user_data["target_user"] = user_id

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, age, city, bio, photo, premium_until, is_banned
        FROM users WHERE telegram_id = %s
    """, (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return

    premium_status = "Да" if user[5] and user[5] > datetime.now() else "Нет"
    banned_status = "Да" if user[6] else "Нет"

    text = f"""
Имя: {user[0]}
Возраст: {user[1]}
Город: {user[2]}
Bio: {user[3]}

Premium: {premium_status}
Бан: {banned_status}
"""

    if user[4]:
        await query.message.reply_photo(user[4], caption=text)
    else:
        await query.message.reply_text(text)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 7 дней", callback_data="prem_7"),
         InlineKeyboardButton("💎 30 дней", callback_data="prem_30")],
        [InlineKeyboardButton("💎 6 мес", callback_data="prem_180"),
         InlineKeyboardButton("💎 1 год", callback_data="prem_365")],
        [InlineKeyboardButton("❌ Снять Premium", callback_data="remove_prem")],
        [InlineKeyboardButton("🚫 Бан", callback_data="ban"),
         InlineKeyboardButton("✅ Разбан", callback_data="unban")],
        [InlineKeyboardButton("🖼 Одобрить фото", callback_data="approve_photo"),
         InlineKeyboardButton("🗑 Удалить фото", callback_data="delete_photo")]
    ])

    await query.message.reply_text("Управление:", reply_markup=keyboard)


# ================= PREMIUM =================

async def give_premium(update, context):
    query = update.callback_query
    await query.answer()

    days = int(query.data.split("_")[1])
    user_id = context.user_data.get("target_user")

    activate_premium(user_id, days)
    await query.message.reply_text(f"✅ Premium выдан на {days} дней.")


async def remove_prem(update, context):
    query = update.callback_query
    await query.answer()

    user_id = context.user_data.get("target_user")
    remove_premium(user_id)

    await query.message.reply_text("❌ Premium снят.")


# ================= БАН =================

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


# ================= ФОТО =================

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


# ================= МОДЕРАЦИЯ =================

async def moderation_photos(update, context):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT telegram_id, name FROM users
        WHERE photo_approved = FALSE AND photo IS NOT NULL
    """)
    users = cur.fetchall()
    cur.close()
    conn.close()

    if not users:
        await query.message.reply_text("Нет фото на модерации.")
        return

    buttons = [
        [InlineKeyboardButton(f"{u[1]} ({u[0]})", callback_data=f"user_{u[0]}")]
        for u in users
    ]

    await query.message.reply_text(
        "Фото на проверке:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ================= СТАТИСТИКА =================

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


# ================= РАССЫЛКА =================

async def start_broadcast(update, context):
    query = update.callback_query
    await query.answer()
    context.user_data["broadcast"] = True
    await query.message.reply_text("Введите текст рассылки:")


async def send_broadcast(update, context):
    if not context.user_data.get("broadcast"):
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

    await update.message.reply_text("✅ Рассылка завершена.")
    context.user_data.clear()


# ================= HANDLERS =================

def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),
        CallbackQueryHandler(show_users, pattern="admin_users"),
        CallbackQueryHandler(user_profile, pattern="user_"),
        CallbackQueryHandler(give_premium, pattern="prem_"),
        CallbackQueryHandler(remove_prem, pattern="remove_prem"),
        CallbackQueryHandler(ban, pattern="ban"),
        CallbackQueryHandler(unban, pattern="unban"),
        CallbackQueryHandler(approve, pattern="approve_photo"),
        CallbackQueryHandler(delete, pattern="delete_photo"),
        CallbackQueryHandler(moderation_photos, pattern="admin_photos"),
        CallbackQueryHandler(show_stats, pattern="admin_stats"),
        CallbackQueryHandler(start_broadcast, pattern="admin_broadcast"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast),
    ]
