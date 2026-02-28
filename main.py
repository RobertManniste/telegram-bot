from telegram.ext import ApplicationBuilder
from database import create_tables
from admin import admin_handlers
from matching import matching_handlers
from registration import registration_handlers
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    create_tables()

    for h in registration_handlers():
        app.add_handler(h)

    for h in matching_handlers():
        app.add_handler(h)

    for h in admin_handlers():
        app.add_handler(h)

    app.run_polling()

if __name__ == "__main__":
    main()
