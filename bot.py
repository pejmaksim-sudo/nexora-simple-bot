
import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

SERVICE, TASK, LOCATION, DATE, CONTACT = range(5)

def menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📝 Оставить заявку")],
            [KeyboardButton("ℹ️ Как работает NEXORA"),
             KeyboardButton("📞 Связаться с менеджером")]
        ],
        resize_keyboard=True
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Добро пожаловать в NEXORA!\n\n"
        "Мы помогаем найти подходящего специалиста под вашу задачу в Магнитогорске.\n\n"
        "Нажмите «📝 Оставить заявку», чтобы начать.",
        reply_markup=menu()
    )
    return ConversationHandler.END

async def begin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🔧 Какая услуга вам нужна?\n\n"
        "Например: сантехника, электрика, ремонт, авто, перевозка."
    )
    return SERVICE

async def service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["service"] = update.message.text
    await update.message.reply_text("📝 Опишите, что именно нужно сделать.")
    return TASK

async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task"] = update.message.text
    await update.message.reply_text("📍 Где находится объект?\n\nРайон или адрес.")
    return LOCATION

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["location"] = update.message.text
    await update.message.reply_text("📅 Когда нужен специалист?")
    return DATE

async def date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date"] = update.message.text
    await update.message.reply_text(
        "📞 Оставьте номер телефона.\n\n"
        "Можно нажать кнопку ниже или написать номер вручную.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Отправить номер", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return CONTACT

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text

    context.user_data["contact"] = phone
    u = update.effective_user
    d = context.user_data

    username = f"@{u.username}" if u.username else "нет username"

    text = (
        "🔔 НОВАЯ ЗАЯВКА NEXORA\n\n"
        f"🔧 Услуга: {d['service']}\n"
        f"📝 Задача: {d['task']}\n"
        f"📍 Место: {d['location']}\n"
        f"📅 Когда: {d['date']}\n"
        f"📞 Телефон: {d['contact']}\n"
        f"👤 Telegram: {username}\n"
        f"🆔 ID клиента: {u.id}"
    )

    if ADMIN_CHAT_ID:
        await context.bot.send_message(ADMIN_CHAT_ID, text)

    await update.message.reply_text(
        "✅ Заявка принята!\n\n"
        "Спасибо за обращение в NEXORA.\n"
        "Менеджер получил вашу заявку и свяжется с вами.",
        reply_markup=menu()
    )

    context.user_data.clear()
    return ConversationHandler.END

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Как работает NEXORA:\n\n"
        "1️⃣ Вы оставляете заявку.\n"
        "2️⃣ Мы уточняем задачу.\n"
        "3️⃣ Подбираем подходящего специалиста.\n"
        "4️⃣ Связываемся с вами.\n\n"
        "NEXORA — быстро находим исполнителя под вашу задачу.",
        reply_markup=menu()
    )

async def manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Связаться с менеджером можно напрямую.\n\n"
        "Напишите сообщение следующим сообщением — я передам его менеджеру."
    )
    context.user_data["manager_message"] = True

async def manager_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("manager_message") and ADMIN_CHAT_ID:
        u = update.effective_user
        username = f"@{u.username}" if u.username else "нет username"
        await context.bot.send_message(
            ADMIN_CHAT_ID,
            f"📞 СООБЩЕНИЕ МЕНЕДЖЕРУ\n\n"
            f"От: {username}\n"
            f"ID: {u.id}\n\n"
            f"{update.message.text}"
        )
        await update.message.reply_text(
            "✅ Сообщение передано менеджеру.",
            reply_markup=menu()
        )
        context.user_data.clear()
        return
    await update.message.reply_text(
        "Используйте кнопки меню.",
        reply_markup=menu()
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Заявка отменена.",
        reply_markup=menu()
    )
    return ConversationHandler.END

app = Application.builder().token(TOKEN).build()

conv = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex("^📝 Оставить заявку$"), begin)
    ],
    states={
        SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, service)],
        TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, task)],
        LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
        DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, date)],
        CONTACT: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), contact)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(conv)
app.add_handler(MessageHandler(filters.Regex("^ℹ️ Как работает NEXORA$"), info))
app.add_handler(MessageHandler(filters.Regex("^📞 Связаться с менеджером$"), manager))
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        manager_message
    )
)

print("NEXORA bot started")
app.run_polling(allowed_updates=Update.ALL_TYPES)
