import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

TOKEN = os.environ.get("BOT_TOKEN")
URL   = os.environ.get("RENDER_EXTERNAL_URL")

if not TOKEN or not URL:
    raise RuntimeError("Не заданы BOT_TOKEN или RENDER_EXTERNAL_URL")

# Telegram Application
app_bot = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен!")

app_bot.add_handler(CommandHandler("start", start))


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


# ===== SHUTDOWN =====
@app.on_event("shutdown")
async def shutdown_event():
    print("Остановка бота...")
    await app_bot.stop()
    await app_bot.shutdown()
