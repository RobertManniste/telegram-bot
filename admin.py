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
    activate_premium
)

ADMIN_ID = int(os.getenv("ADMIN_ID"))


# ================= ПРОВЕРКА АДМИНА =================

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

    if not users:
        await query.message.reply_text("Пользователей нет.")
        return

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
        await query.message.reply_text("Пользователь не найден.")
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

    # --- отправка профиля ---
    if user[4]:
        try:
            await query.message.reply_photo(user[4], caption=text)
        except:
            await query.message.reply_text(text)
    else:
        await query.message.reply_text(text)

    # --- кнопки управления ---
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 7 дней", callback_data="prem_7"),
         InlineKeyboardButton("💎 30 дней", callback_data="prem_30")],
        [InlineKeyboardButton("💎 6 мес", callback_data="prem_180"),
         InlineKeyboardButton("💎 1 год", callback_data="prem_365")],
        [InlineKeyboardButton("❌ Снять Premium", callback_data="remove_prem")],
        [InlineKeyboardButton("🚫 Бан", callback_data="ban"),
         InlineKeyboardButton("✅ Разбан", callback_data="unban")]
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


async def remove_premium_admin(update, context):
    query = update.callback_query
    await query.answer()

    user_id = context.user_data.get("target_user")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET premium_until = NULL WHERE telegram_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    await query.message.reply_text("❌ Premium снят.")


# ================= БАН =================

async def ban_user_admin(update, context):
    query = update.callback_query
    await query.answer()

    user_id = context.user_data.get("target_user")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_banned = TRUE WHERE telegram_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    await query.message.reply_text("🚫 Пользователь забанен.")


async def unban_user_admin(update, context):
    query = update.callback_query
    await query.answer()

    user_id = context.user_data.get("target_user")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_banned = FALSE WHERE telegram_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    await query.message.reply_text("✅ Пользователь разбанен.")


# ================= СТАТИСТИКА =================

async def show_stats(update, context):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE premium_until > NOW()")
    premium = cur.fetchone()[0]

    cur.close()
    conn.close()

    text = f"""
📊 Статистика

Пользователи: {users}
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
        CallbackQueryHandler(remove_premium_admin, pattern="remove_prem"),
        CallbackQueryHandler(ban_user_admin, pattern="ban"),
        CallbackQueryHandler(unban_user_admin, pattern="unban"),
        CallbackQueryHandler(show_stats, pattern="admin_stats"),
        CallbackQueryHandler(start_broadcast, pattern="admin_broadcast"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast),
    ]
