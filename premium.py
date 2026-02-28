import os
import psycopg2
from telegram import LabeledPrice, Update
from telegram.ext import ContextTypes


PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


async def send_premium_invoice(update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id

    prices = [LabeledPrice("Premium подписка", 699)]  # 999 Stars

    await context.bot.send_invoice(
        chat_id=chat_id,
        title="💎 Europe Match Premium",
        description="Безлимитные сообщения и полный доступ ко всем функциям.",
        payload="premium_payment",
        provider_token=PROVIDER_TOKEN,
        currency="XTR",  # Telegram Stars
        prices=prices,
        start_parameter="premium",
    )


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET premium=TRUE,
            trial_end=NULL,
            messages_today=0
        WHERE telegram_id=%s
    """, (user_id,))

    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text("🎉 Premium активирован! Теперь у вас нет ограничений.")
