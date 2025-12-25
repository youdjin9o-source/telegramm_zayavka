import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# СТАНИ
CHOOSING_PERSON, ENTER_DATETIME, ENTER_TEXT = range(3)

# Кнопки
main_menu = ReplyKeyboardMarkup(
    [["Нагадати"], ["Список нагадувань"], ["Скасувати"]],
    resize_keyboard=True
)
people_menu = ReplyKeyboardMarkup(
    [["Ярослав", "Анна", "Єгор"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Гаразд, поїхали. Обери дію:", reply_markup=main_menu)
    return CHOOSING_PERSON

async def choose_person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Нагадати":
        await update.message.reply_text("Кому нагадати?", reply_markup=people_menu)
        return ENTER_DATETIME
    await update.message.reply_text("Вибери нормально.", reply_markup=main_menu)
    return CHOOSING_PERSON

async def get_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["person"] = update.message.text
    await update.message.reply_text("Введи дату і час у форматі ДД.ММ ГГ:ХХ")
    return ENTER_TEXT

async def get_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["datetime"] = update.message.text
    await update.message.reply_text("Окей, а тепер текст нагадування:")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано. Як твої плани на завтра? Та неважливо.", reply_markup=main_menu)
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_PERSON: [MessageHandler(filters.TEXT, choose_person)],
            ENTER_DATETIME: [MessageHandler(filters.TEXT, get_datetime)],
            ENTER_TEXT: [MessageHandler(filters.TEXT, get_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
