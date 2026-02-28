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


# ================= CHECK ADMIN =================

def is_admin(user_id):
    return user_id == ADMIN_ID


# ================= MENU =================

async def admin_panel(update, context):
    if not is_admin(update.effective_user.id):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("💎 Premium", callback_data="admin_premium")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📨 Рассылка", callback_data="admin_broadcast")]
    ])

    await update.message.reply_text("⚙ Админ панель", reply_markup=keyboard)


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

    if not users:
        await query.message.reply_text("Пользователей нет.")
        return

    buttons = []
    for u in users:
        buttons.append([InlineKeyboardButton(f"{u[1]} ({u[0]})", callback_data=f"user_{u[0]}")])

    await query.message.reply_text(
        "👥 Список пользователей:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ================= USER PROFILE =================

async def show_user_profile(update, context):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, age, city, bio, premium_until
        FROM users WHERE telegram_id = %s
    """, (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return

    premium_status = "Да" if user[4] and user[4] > datetime.now() else "Нет"

    text = f"""
Имя: {user[0]}
Возраст: {user[1]}
Город: {user[2]}
Bio: {user[3]}
Premium: {premium_status}
"""

    await query.message.reply_text(text)


# ================= PREMIUM =================

async def premium_menu(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("7 дней", callback_data="prem_7")],
        [InlineKeyboardButton("30 дней", callback_data="prem_30")],
        [InlineKeyboardButton("6 месяцев", callback_data="prem_180")],
        [InlineKeyboardButton("1 год", callback_data="prem_365")]
    ])

    await query.message.reply_text("Выберите срок Premium:", reply_markup=keyboard)


async def ask_user_for_premium(update, context):
    query = update.callback_query
    await query.answer()

    days = int(query.data.split("_")[1])
    context.user_data["premium_days"] = days

    await query.message.reply_text("Введите Telegram ID пользователя:")


async def set_premium(update, context):
    if "premium_days" not in context.user_data:
        return

    try:
        user_id = int(update.message.text)
    except:
        await update.message.reply_text("Введите корректный ID.")
        return

    activate_premium(user_id, context.user_data["premium_days"])
    await update.message.reply_text("✅ Premium успешно выдан.")

    context.user_data.clear()


# ================= STATS =================

async def show_stats(update, context):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM likes")
    total_likes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM matches")
    total_matches = cur.fetchone()[0]

    cur.close()
    conn.close()

    text = f"""
📊 Статистика

Пользователи: {total_users}
Лайки: {total_likes}
Матчи: {total_matches}
"""

    await query.message.reply_text(text)


# ================= BROADCAST =================

async def start_broadcast(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["broadcast"] = True
    await query.message.reply_text("Введите текст для рассылки:")


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
            await context.bot.send_message(chat_id=u[0], text=text)
        except:
            pass

    await update.message.reply_text("✅ Рассылка завершена.")
    context.user_data.clear()


# ================= HANDLERS =================

def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),
        CallbackQueryHandler(show_users, pattern="admin_users"),
        CallbackQueryHandler(show_user_profile, pattern="user_"),
        CallbackQueryHandler(premium_menu, pattern="admin_premium"),
        CallbackQueryHandler(ask_user_for_premium, pattern="prem_"),
        CallbackQueryHandler(show_stats, pattern="admin_stats"),
        CallbackQueryHandler(start_broadcast, pattern="admin_broadcast"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, set_premium),
        MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast),
    ]
