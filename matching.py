import os
import psycopg2
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, ContextTypes, filters


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


# ================== ПОКАЗ АНКЕТ ==================

async def browse_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
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


# ================== ЛАЙКИ ==================

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    target_id = int(query.data.split("_")[1])

    conn = get_connection()
    cur = conn.cursor()

    # сохраняем лайк
    cur.execute("""
        INSERT INTO likes (user_id, liked_user_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (user_id, target_id))

    # проверяем взаимность
    cur.execute("""
        SELECT 1 FROM likes
        WHERE user_id=%s AND liked_user_id=%s
    """, (target_id, user_id))

    match = cur.fetchone()

    if match:
        await query.message.reply_text("💘 У вас совпадение! Теперь можете общаться.")

    conn.commit()
    cur.close()
    conn.close()

    await browse_profiles(update, context)


# ================== ПЕРЕСЫЛКА СООБЩЕНИЙ ==================

async def forward_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    conn = get_connection()
    cur = conn.cursor()

    # проверяем premium и trial
    cur.execute("""
        SELECT premium, trial_end, messages_today
        FROM users WHERE telegram_id=%s
    """, (user_id,))
    user = cur.fetchone()

    if not user:
        return

    premium, trial_end, messages_today = user

    if not premium:
        if trial_end is None:
            await update.message.reply_text(
                "⛔ У вас закончилась пробная версия.\n"
                "Купите Premium и общайтесь без ограничений."
            )
            return

        if messages_today >= 20:
            await update.message.reply_text(
                "⛔ Лимит 20 сообщений в день исчерпан.\n"
                "Купите Premium 💎"
            )
            return

        cur.execute("""
            UPDATE users
            SET messages_today = messages_today + 1
            WHERE telegram_id=%s
        """, (user_id,))

    # получаем все матчи
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
        context.bot.send_message(match[0], f"💬 Сообщение:\n{text}")

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
