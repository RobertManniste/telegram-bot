import os
import psycopg2
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# ===== ПОЛУЧИТЬ СЛУЧАЙНУЮ АНКЕТУ =====
def get_random_profile(viewer_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT telegram_id, name, age, city, bio, photo
        FROM users
        WHERE telegram_id != %s
        ORDER BY RANDOM()
        LIMIT 1
    """, (viewer_id,))

    profile = cur.fetchone()

    cur.close()
    conn.close()
    return profile


# ===== ПРОВЕРКА ВЗАИМНОГО ЛАЙКА =====
def is_match(user1, user2):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 1 FROM likes 
        WHERE from_user = %s AND to_user = %s
    """, (user2, user1))

    result = cur.fetchone()

    cur.close()
    conn.close()
    return result is not None


# ===== СОХРАНИТЬ ЛАЙК =====
def save_like(from_user, to_user):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO likes (from_user, to_user)
        VALUES (%s, %s)
    """, (from_user, to_user))

    conn.commit()
    cur.close()
    conn.close()


# ===== ПОКАЗ АНКЕТЫ =====
async def browse_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    profile = get_random_profile(user_id)

    if not profile:
        await update.message.reply_text("Пока нет доступных анкет 😔")
        return

    target_id, name, age, city, bio, photo = profile

    context.user_data["current_profile"] = target_id

    caption = f"""
{name}, {age}
📍 {city}

{bio}
"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👍 Нравится", callback_data="like"),
            InlineKeyboardButton("👎 Пропустить", callback_data="skip"),
        ]
    ])

    await update.message.reply_photo(photo=photo, caption=caption, reply_markup=keyboard)


# ===== ОБРАБОТКА ЛАЙКОВ =====
async def handle_swipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    target_id = context.user_data.get("current_profile")

    if not target_id:
        await query.message.reply_text("Ошибка. Попробуйте снова.")
        return

    if query.data == "like":
        save_like(user_id, target_id)

        if is_match(user_id, target_id):
            await query.message.reply_text("💘 У вас совпадение!")
            await context.bot.send_message(
                chat_id=target_id,
                text="💘 У вас новое совпадение!"
            )

        else:
            await query.message.reply_text("Лайк отправлен ❤️")

    # показать следующую анкету
    await browse_profiles(query, context)


def matching_handlers():
    return [
        CommandHandler("browse", browse_profiles),
        CallbackQueryHandler(handle_swipe, pattern="^(like|skip)$"),
    ]
