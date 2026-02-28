import os
import psycopg2
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, ContextTypes, filters


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


# ================== ПРОВЕРКА PREMIUM ==================

def is_premium_active(premium_until):
    if not premium_until:
        return False
    return premium_until > datetime.utcnow()


# ================== ПОКАЗ АНКЕТ ==================

async def browse_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT telegram_id, name, age, bio
        FROM users
        WHERE telegram_id != %s
        ORDER BY RANDOM()
        LIMIT 1
    """, (user_id,))

    profile = cur.fetchone()

    cur.close()
    conn.close()

    if not profile:
        await query.message.reply_text("Анкет пока нет 😔")
        return

    target_id, name, age, bio = profile

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❤️", callback_data=f"like_{target_id}"),
            InlineKeyboardButton("❌", callback_data="next")
        ]
    ])

    await query.message.reply_text(
        f"{name}, {age}\n\n{bio}",
        reply_markup=keyboard
    )


# ================== ЛАЙК ==================

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    target_id = int(query.data.split("_")[1])

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO likes (user_id, liked_user_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (user_id, target_id))

    cur.execute("""
        SELECT 1 FROM likes
        WHERE user_id=%s AND liked_user_id=%s
    """, (target_id, user_id))

    match = cur.fetchone()

    if match:
        await query.message.reply_text("💘 У вас совпадение!")

    conn.commit()
    cur.close()
    conn.close()

    await browse_profiles(update, context)


# ================== СООБЩЕНИЯ ==================

async def forward_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT premium_until, trial_end, messages_today
        FROM users WHERE telegram_id=%s
    """, (user_id,))

    user = cur.fetchone()

    if not user:
        return

    premium_until, trial_end, messages_today = user
    premium_active = is_premium_active(premium_until)

    if not premium_active:
        if not trial_end:
            await update.message.reply_text(
                "⛔ Пробная версия закончилась.\nКупите Premium."
            )
            return

        if messages_today >= 20:
            await update.message.reply_text(
                "⛔ Лимит 20 сообщений в день.\nКупите Premium."
            )
            return

        cur.execute("""
            UPDATE users
            SET messages_today = messages_today + 1
            WHERE telegram_id=%s
        """, (user_id,))

    # Получаем взаимные матчи
    cur.execute("""
        SELECT l2.user_id
        FROM likes l1
        JOIN likes l2
        ON l1.user_id = l2.liked_user_id
        AND l1.liked_user_id = l2.user_id
        WHERE l1.user_id=%s
    """, (user_id,))

    matches = cur.fetchall()

    for match in matches:
        await context.bot.send_message(match[0], f"💬 {text}")

    conn.commit()
    cur.close()
    conn.close()


# ================== HANDLERS ==================

def matching_handlers():
    return [
        CallbackQueryHandler(handle_like, pattern="^like_"),
        CallbackQueryHandler(browse_profiles, pattern="^next$"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, forward_messages)
    ]
