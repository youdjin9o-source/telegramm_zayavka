import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes, CallbackQueryHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Словник користувачів
USERS = {
    "Єгор": 6673177017,
    "Ярослав": 7754277795,
    "Анна": 1223902928
}

# Список нагадувань у пам'яті
reminders = []

# Стан конверсії
CHOOSING_ACTION, CHOOSING_PERSON, ENTER_DATETIME, ENTER_TEXT = range(4)

scheduler = AsyncIOScheduler()
scheduler.start()

# Кнопки
main_menu = ReplyKeyboardMarkup(
    [["Нагадати"], ["Список нагадувань"], ["Скасувати"]],
    resize_keyboard=True
)
people_menu = ReplyKeyboardMarkup(
    [["Єгор", "Ярослав", "Анна"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Обери дію:", reply_markup=main_menu)
    return CHOOSING_ACTION

async def choosing_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Нагадати":
        await update.message.reply_text("Кому нагадати?", reply_markup=people_menu)
        return CHOOSING_PERSON
    elif text == "Список нагадувань":
        if not reminders:
            await update.message.reply_text("Поки немає нагадувань.")
        else:
            msg = "\n".join([f"{r['person']} | {r['datetime']} | {r['text']}" for r in reminders])
            await update.message.reply_text("Нагадування:\n" + msg)
        return CHOOSING_ACTION
    elif text == "Скасувати":
        await update.message.reply_text("Скасовано.", reply_markup=main_menu)
        return CHOOSING_ACTION
    else:
        await update.message.reply_text("Оберіть кнопку.", reply_markup=main_menu)
        return CHOOSING_ACTION

async def choosing_person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    person = update.message.text
    if person not in USERS:
        await update.message.reply_text("Оберіть одного з користувачів.", reply_markup=people_menu)
        return CHOOSING_PERSON
    context.user_data["person"] = person
    await update.message.reply_text("Введи дату та час у форматі ДД.MM ЧЧ:ММ (наприклад 27.01 16:00)")
    return ENTER_DATETIME

async def enter_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dt_str = update.message.text
    try:
        dt = datetime.strptime(dt_str, "%d.%m %H:%M")
        context.user_data["datetime"] = dt
        await update.message.reply_text("Введи текст нагадування:")
        return ENTER_TEXT
    except:
        await update.message.reply_text("Неправильний формат. Спробуй ще раз: ДД.MM ЧЧ:ММ")
        return ENTER_DATETIME

async def enter_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    person = context.user_data["person"]
    dt = context.user_data["datetime"]

    # зберігаємо нагадування
    reminder = {"person": person, "datetime": dt, "text": text}
    reminders.append(reminder)

    # створюємо кнопку ✔️
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✔️ Зробив", callback_data=f"done_{len(reminders)-1}")]])

    # плануємо відправку
    scheduler.add_job(
        send_reminder,
        'date',
        run_date=dt,
        args=[USERS[person], text, keyboard]
    )

    await update.message.reply_text(f"Нагадування для {person} збережено.", reply_markup=main_menu)
    return CHOOSING_ACTION

async def send_reminder(chat_id, text, keyboard):
    await app.bot.send_message(chat_id, f"⏰ Нагадування:\n{text}", reply_markup=keyboard)

async def done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # done_0, done_1...
    index = int(data.split("_")[1])
    reminder = reminders[index]
    # повідомляємо батьків (Ярослав та Анна)
    for parent in ["Ярослав", "Анна"]:
        if parent != reminder["person"]:  # щоб не надсилати тому, хто виконав
            await context.bot.send_message(USERS[parent], f"{reminder['person']} виконав: {reminder['text']}")
    await query.edit_message_text(f"✅ Виконано: {reminder['text']}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано.", reply_markup=main_menu)
    return CHOOSING_ACTION

# Створюємо Application
app = Application.builder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSING_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choosing_action)],
        CHOOSING_PERSON: [MessageHandler(filters.TEXT & ~filters.COMMAND, choosing_person)],
        ENTER_DATETIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_datetime)],
        ENTER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_text)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(done_callback, pattern=r"done_\d+"))

if __name__ == "__main__":
    app.run_polling()
