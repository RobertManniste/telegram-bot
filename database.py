import os
import psycopg2
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

ADMIN_ID = int(os.getenv("ADMIN_ID"))


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def is_admin(user_id):
    return user_id == ADMIN_ID


# ===================== ГЛАВНАЯ ПАНЕЛЬ =====================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Нет доступа")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("💎 Premium", callback_data="admin_premium")],
        [InlineKeyboardButton("🖼 Фото на проверке", callback_data="admin_photos")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")]
    ])

    await update.message.reply_text("⚙ Админ панель", reply_markup=keyboard)


# ===================== СТАТИСТИКА =====================

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


# ===================== ПОЛЬЗОВАТЕЛИ =====================

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT telegram_id, name, premium FROM users")
    users = cur.fetchall()

    cur.close()
    conn.close()

    text = "👥 Пользователи:\n\n"

    for user in users:
        text += f"ID: {user[0]} | {user[1]} | Premium: {user[2]}\n"

    await query.message.reply_text(text)


# ===================== РАССЫЛКА =====================

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["broadcast"] = True
    await query.message.reply_text("✍ Введите текст для рассылки:")


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("broadcast"):
        return

    text = update.message.text

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT telegram_id FROM users")
    users = cur.fetchall()

    cur.close()
    conn.close()

    for user in users:
        try:
            await context.bot.send_message(user[0], f"📢 Сообщение от администрации:\n\n{text}")
        except:
            pass

    context.user_data["broadcast"] = False
    await update.message.reply_text("✅ Рассылка завершена")


# ===================== ВЫДАЧА PREMIUM =====================

async def give_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("Введите ID пользователя для выдачи Premium:")
    context.user_data["give_premium"] = True


async def process_give_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("give_premium"):
        return

    user_id = int(update.message.text)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("UPDATE users SET premium=TRUE WHERE telegram_id=%s", (user_id,))
    conn.commit()

    cur.close()
    conn.close()

    context.user_data["give_premium"] = False
    await update.message.reply_text("💎 Premium выдан")


# ===================== ПРОВЕРКА ФОТО =====================

async def check_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT telegram_id, photo_file_id FROM users WHERE photo_file_id IS NOT NULL")
    photos = cur.fetchall()

    cur.close()
    conn.close()

    for photo in photos:
        user_id, file_id = photo

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Оставить", callback_data=f"photo_ok_{user_id}"),
                InlineKeyboardButton("❌ Удалить", callback_data=f"photo_delete_{user_id}")
            ]
        ])

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=f"Фото пользователя ID: {user_id}",
            reply_markup=keyboard
        )


async def delete_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[-1])

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("UPDATE users SET photo_file_id=NULL WHERE telegram_id=%s", (user_id,))
    conn.commit()

    cur.close()
    conn.close()

    await query.message.reply_text("🗑 Фото удалено")


# ===================== HANDLERS =====================

def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),

        CallbackQueryHandler(show_stats, pattern="admin_stats"),
        CallbackQueryHandler(list_users, pattern="admin_users"),
        CallbackQueryHandler(start_broadcast, pattern="admin_broadcast"),
        CallbackQueryHandler(give_premium, pattern="admin_premium"),
        CallbackQueryHandler(check_photos, pattern="admin_photos"),
        CallbackQueryHandler(delete_photo, pattern="photo_delete_"),

        MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message),
        MessageHandler(filters.TEXT & ~filters.COMMAND, process_give_premium),
    ]
