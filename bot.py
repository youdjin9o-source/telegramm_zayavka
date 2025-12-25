import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ConversationHandler,
    ContextTypes, CallbackQueryHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Ролі
PARENTS = ["Ярослав", "Анна"]
CHILD = "Єгор"

USERS = {
    "Єгор": 6673177017,
    "Ярослав": 7754277795,
    "Анна": 1223902928
}

# Пам'ять нагадувань
reminders = []

# Стан конверсії
CHOOSING_ACTION, CHOOSING_PERSON, ENTER_DATETIME, ENTER_TEXT = range(4)

scheduler = AsyncIOScheduler()
scheduler.start()

# Кнопки
main_menu_parent = ReplyKeyboardMarkup(
    [["Нагадати"], ["Список нагадувань"], ["Скасувати"]],
    resize_keyboard=True
)
main_menu_child = ReplyKeyboardMarkup(
    [["Список нагадувань"]],
    resize_keyboard=True
)
people_menu = ReplyKeyboardMarkup(
    [["Єгор", "Ярослав", "Анна"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    role_menu = main_menu_parent if user_id in [USERS[p] for p in PARENTS] else main_menu_child
    await update.message.reply_text("Привіт! Обери дію:", reply_markup=role_menu)
    return CHOOSING_ACTION

async def choosing_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "Нагадати" and user_id in [USERS[p] for p in PARENTS]:
        await update.message.reply_text("Кому нагадати?", reply_markup=people_menu)
        return CHOOSING_PERSON
    elif text == "Список нагадувань":
        user_reminders = [r for r in reminders if r["person_id"] == user_id]
        if not user_reminders:
            await update.message.reply_text("Нагадувань немає.")
        else:
            msg = "\n".join([f"{r['datetime'].strftime('%d.%m %H:%M')} — {r['text']}" for r in user_reminders])
            await update.message.reply_text(msg)
        return CHOOSING_ACTION
    elif text == "Скасувати":
        await update.message.reply_text("Скасовано.", reply_markup=main_menu_parent)
        return CHOOSING_ACTION
    else:
        await update.message.reply_text("Оберіть кнопку правильно.")
        return CHOOSING_ACTION

async def choosing_person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    person = update.message.text
    if person not in USERS:
        await update.message.reply_text("Оберіть одного з користувачів.", reply_markup=people_menu)
        return CHOOSING_PERSON
    context.user_data["person_name"] = person
    context.user_data["person_id"] = USERS[person]
    await update.message.reply_text("Введи дату і час у форматі ДД.MM ЧЧ:ММ")
    return ENTER_DATETIME

async def enter_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dt_str = update.message.text
    try:
        dt = datetime.strptime(dt_str, "%d.%m %H:%M")
        context.user_data["datetime"] = dt
        await update.message.reply_text("Введи текст нагадування:")
        return ENTER_TEXT
    except:
        await update.message.reply_text("Неправильний формат. Спробуй: ДД.MM ЧЧ:ММ")
        return ENTER_DATETIME

async def enter_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    reminder = {
        "person_name": context.user_data["person_name"],
        "person_id": context.user_data["person_id"],
        "datetime": context.user_data["datetime"],
        "text": text
    }
    reminders.append(reminder)

    # Кнопка ✔️
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✔️ Зробив", callback_data=f"done_{len(reminders)-1}")]])

    # Плануємо нагадування
    scheduler.add_job(
        lambda: asyncio.create_task(send_reminder(reminder["person_id"], reminder["text"], keyboard)),
        'date',
        run_date=reminder["datetime"]
    )

    await update.message.reply_text(f"Нагадування для {reminder['person_name']} збережено.", reply_markup=main_menu_parent)
    return CHOOSING_ACTION

async def send_reminder(chat_id, text, keyboard):
    await app.bot.send_message(chat_id, f"⏰ Нагадування:\n{text}", reply_markup=keyboard)

async def done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.split("_")[1])
    reminder = reminders[index]

    # Повідомляємо батьків
    for parent in PARENTS:
        if USERS[parent] != reminder["person_id"]:
            await context.bot.send_message(USERS[parent], f"{reminder['person_name']} виконав: {reminder['text']}")
    await query.edit_message_text(f"✅ Виконано: {reminder['text']}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано.", reply_markup=main_menu_parent)
    return CHOOSING_ACTION

app = Application.builder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSING_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choosing_action)],
        CHOOSING_PERSON: [MessageHandler(filters.TEXT & ~filters.COMMAND, choosing_person)],
        ENTER_DATETIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_datetime)],
        ENTER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_text)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(done_callback, pattern=r"done_\d+"))

if __name__ == "__main__":
    app.run_polling()
