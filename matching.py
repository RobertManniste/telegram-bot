import os
import psycopg2
from datetime import datetime, date
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


# ===== ПОЛУЧЕНИЕ ДАННЫХ ПОЛЬЗОВАТЕЛЯ =====
def get_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT premium, trial_end, messages_today, last_message_date
        FROM users WHERE telegram_id=%s
    """, (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


def update_message_count(user_id):
    conn = get_connection()
    cur = conn.cursor()

    today = date.today()

    cur.execute("""
        SELECT messages_today, last_message_date
        FROM users WHERE telegram_id=%s
    """, (user_id,))

    messages_today, last_date = cur.fetchone()

    if last_date != today:
        messages_today = 0

    messages_today += 1

    cur.execute("""
        UPDATE users
        SET messages_today=%s, last_message_date=%s
        WHERE telegram_id=%s
    """, (messages_today, today, user_id))

    conn.commit()
    cur.close()
    conn.close()


# ===== ПРОВЕРКА ЛИМИТОВ =====
def can_send_message(user_id):
    user = get_user(user_id)
    if not user:
        return False, "Вы не зарегистрированы."

    premium, trial_end, messages_today, last_date = user

    # Premium — безлимит
    if premium:
        return True, None

    # Проверка trial
    if trial_end and datetime.now() > trial_end:
        return False, "⛔ Пробный период завершён. Купите Premium."

    # Проверка лимита 20
    today = date.today()
    if last_date != today:
        messages_today = 0

    if messages_today >= 20:
        return False, "⛔ Лимит 20 сообщений в день исчерпан."

    return True, None


# ===== МАТЧИ =====
def get_matches(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT user1, user2 FROM matches
        WHERE user1=%s OR user2=%s
    """, (user_id, user_id))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    partners = []
    for u1, u2 in rows:
        partners.append(u2 if u1 == user_id else u1)

    return partners


# ===== ПЕРЕСЫЛКА СООБЩЕНИЙ =====
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    allowed, error = can_send_message(user_id)
    if not allowed:
        await update.message.reply_text(error)
        return

    matches = get_matches(user_id)

    if not matches:
        return

    # увеличиваем счётчик
    update_message_count(user_id)

    for partner in matches:
        await context.bot.send_message(
            chat_id=partner,
            text=f"💬 Сообщение от совпадения:\n\n{update.message.text}"
        )


# ===== HANDLERS =====
def matching_handlers():
    return [
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages),
    ]
