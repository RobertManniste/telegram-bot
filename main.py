
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

users = {}

# =======================
# Проверка Trial
# =======================

def is_trial_active(user):
    return datetime.now() < user["trial_until"]

# =======================
# /start
# =======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in users:
        users[user_id] = {
            "premium": False,
            "trial_until": datetime.now() + timedelta(days=3),
            "messages_today": 0,
            "last_message_date": datetime.now().date()
        }

    keyboard = [
        [InlineKeyboardButton("📸 Смотреть фото", callback_data="view_photo")],
        [InlineKeyboardButton("💎 Купить Premium (999⭐)", callback_data="buy_premium")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "💙 Добро пожаловать в Europe Match\n\n"
        "Мы объединяем людей по всей Европе для знакомств, общения и серьёзных отношений.\n"
        "Найди свою вторую половинку быстро и безопасно 🌍\n\n"
        "🎁 Вам доступен пробный период 3 дня!\n\n"
        "В пробной версии:\n"
        "• 20 сообщений в день\n"
        "• Частичный доступ к фотографиям\n"
        "• Возможность начать общение\n\n"
        "💎 Premium открывает:\n"
        "• Неограниченные сообщения\n"
        "• Полный доступ ко всем фото\n"
        "• Приоритет профиля\n"
        "• Без ограничений\n\n"
        "Открой больше возможностей 💙"
    )

    await update.message.reply_text(text, reply_markup=reply_markup)

# =======================
# Обработка кнопок
# =======================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user = users.get(user_id)

    if not user:
        await query.message.reply_text("Нажмите /start")
        return

    if query.data == "view_photo":

        # Premium всегда видит
        if user["premium"]:
            await query.message.reply_photo(
                "https://via.placeholder.com/400x500.png?text=Full+Photo"
            )
            return

        # Trial активен
        if is_trial_active(user):
            await query.message.reply_photo(
                "https://via.placeholder.com/400x500.png?text=Trial+Photo"
            )
            return

        await query.message.reply_text(
            "🔒 Фото частично скрыто.\n\n"
            "Купите Premium для полного доступа 💎"
        )

    if query.data == "buy_premium":
        user["premium"] = True
        await query.message.reply_text(
            "💎 Premium активирован!\n\n"
            "Теперь вам доступны:\n"
            "• Безлимитные сообщения\n"
            "• Все фотографии\n"
            "• Приоритет профиля\n\n"
            "Приятных знакомств ❤️"
        )

# =======================
# Ограничение сообщений
# =======================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = users.get(user_id)

    if not user:
        return

    today = datetime.now().date()

    if user["last_message_date"] != today:
        user["messages_today"] = 0
        user["last_message_date"] = today

    # Premium без лимита
    if user["premium"]:
        await update.message.reply_text("Сообщение отправлено 💬")
        return

    # Trial активен
    if is_trial_active(user):
        if user["messages_today"] >= 20:
            await update.message.reply_text(
                "⚠ Лимит 20 сообщений в день достигнут.\n\n"
                "💎 Купите Premium для безлимитного общения."
            )
            return

        user["messages_today"] += 1
        await update.message.reply_text("Сообщение отправлено 💬")
        return

    # Trial закончился
    await update.message.reply_text(
        "⛔ Ваш пробный период закончился.\n\n"
        "💎 Купите Premium для продолжения общения."
    )

# =======================
# MAIN
# =======================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
