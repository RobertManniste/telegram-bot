from telegram import Update
from telegram.ext import ContextTypes


async def send_premium_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 Покупка Premium временно в разработке."
    )
