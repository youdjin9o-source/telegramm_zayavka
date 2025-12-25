import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SITE_LOGIN = os.getenv("SITE_LOGIN")
SITE_PASSWORD = os.getenv("SITE_PASSWORD")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Кидай номер машини, і я попробую щось знайти.")

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    car_number = update.message.text.strip()

    # Тут НЕ хакерство, а авторизований запит, бо логін у тебе.
    response = requests.post(
        "https://твій-сайт.домен/login",
        data={"login": SITE_LOGIN, "password": SITE_PASSWORD}
    )

    # Потім робиш запит до сторінки з пошуком
    search = requests.get(
        f"https://твій-сайт.домен/search?number={car_number}",
        cookies=response.cookies
    )

    # Парсиш результат (по-хорошому через BeautifulSoup)
    # а тут просто як приклад
    if "заявка" in search.text:
        await update.message.reply_text("Ось твоя заявка: №12345")
    else:
        await update.message.reply_text("Нічого не знайшов, йой...")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

app.run_polling()
