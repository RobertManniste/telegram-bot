import os
from telegram import Update, LabeledPrice
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, PreCheckoutQueryHandler, MessageHandler, filters

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

PRICE = 400  # 400 Stars

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
"Добро пожаловать в Europe Match 💙\n\n"
"Ищешь вторую половинку? Мы объединяем людей по всей Европе.\n\n"
"📌 Соблюдайте правила уважения и честного общения.\n\n"
"Нажми /buy чтобы открыть фото 🔒"
)

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = [LabeledPrice("Premium Access", PRICE)]
    
    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title="Открыть фото 🔓",
        description="Доступ к оригинальному фото профиля",
        payload="premium-photo",
        provider_token="",
        currency="XTR",
        prices=prices,
    )

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Оплата прошла успешно ✅\n\nВот оригинальное фото 👇"
    )
    await update.message.reply_photo("https://picsum.photos/500")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("buy", buy))
app.add_handler(PreCheckoutQueryHandler(precheckout))
app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

app.run_polling()
