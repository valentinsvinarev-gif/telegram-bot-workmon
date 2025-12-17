import os
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from datetime import datetime
from telegram import ReplyKeyboardMarkup
from telegram.ext import MessageHandler, filters

DB_PATH = "data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part TEXT NOT NULL,
            shop TEXT NOT NULL,
            ts TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

TOKEN = os.environ.get("BOT_TOKEN")
URL   = os.environ.get("RENDER_EXTERNAL_URL")

if not TOKEN or not URL:
    raise RuntimeError("Не заданы BOT_TOKEN или RENDER_EXTERNAL_URL")

# Telegram Application
app_bot = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  
    keyboard = [
        ["➕ Добавить", "📋 Проверить"],
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=reply_markup
    )
app_bot.add_handler(CommandHandler("start", start))


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text(
            "Использование:\n/add <обозначение> <цех>\n\nПример:\n/add 10.00.00.001 04"
        )
        return

    part, shop = context.args
    ts = datetime.now().strftime("%d.%m.%Y %H:%M")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO movements (part, shop, ts) VALUES (?, ?, ?)",
        (part, shop, ts)
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"Записано:\nДеталь: {part}\nЦех: {shop}\nВремя: {ts}"
    )
app_bot.add_handler(CommandHandler("add", add))


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text(
            "Использование:\n/history <обозначение>"
        )
        return

    part = context.args[0]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT shop, ts FROM movements WHERE part = ? ORDER BY id",
        (part,)
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("Записей не найдено")
        return

    text = f"История детали {part}:\n"
    for shop, ts in rows:
        text += f"{shop} — {ts}\n"

    await update.message.reply_text(text)

app_bot.add_handler(CommandHandler("history", history))

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "➕ Добавить":
        await update.message.reply_text(
            "Введите:\n/add <обозначение> <цех>\n\nПример:\n/add 10.00.00.001 04"
        )

    elif text == "📋 Проверить":
        await update.message.reply_text(
            "Введите:\n/history <обозначение>\n\nПример:\n/history 10.00.00.001"
        )
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))


# ===== Webhook =====
async def webhook(request):
    data = await request.json()
    update = Update.de_json(data, app_bot.bot)
    await app_bot.process_update(update)
    return PlainTextResponse("OK")


async def health(request):
    return PlainTextResponse("OK")


routes = [
    Route("/telegram", webhook, methods=["POST"]),
    Route("/healthcheck", health),
]

app = Starlette(routes=routes)


# ===== STARTUP =====
@app.on_event("startup")
async def startup_event():
    print("Инициализация Telegram Application...")
    await app_bot.initialize()
    await app_bot.start()

    webhook_url = f"{URL}/telegram"
    print(f"Установка webhook: {webhook_url}")
    await app_bot.bot.set_webhook(webhook_url)

    print("Webhook установлен, бот готов к работе")
    
    init_db()
    print("База данных инициализирована")


# ===== SHUTDOWN =====
@app.on_event("shutdown")
async def shutdown_event():
    print("Остановка бота...")
    await app_bot.stop()
    await app_bot.shutdown()

# ===== Команда /add =====





