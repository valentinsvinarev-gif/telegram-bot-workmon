import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

TOKEN = os.environ.get("BOT_TOKEN")
PORT  = int(os.environ.get("PORT", 8000))
URL   = os.environ.get("RENDER_EXTERNAL_URL")  # правильный способ

# Telegram bot
app_bot = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен!")

app_bot.add_handler(CommandHandler("start", start))

# Webhook endpoint
async def webhook(request):
    data = await request.json()
    update = Update.de_json(data, app_bot.bot)
    await app_bot.process_update(update)
    return PlainTextResponse("OK")

# Healthcheck
async def health(request):
    return PlainTextResponse("OK")

routes = [
    Route("/telegram", webhook, methods=["POST"]),
    Route("/healthcheck", health),
]

app = Starlette(routes=routes)

# Set webhook on startup
@app.on_event("startup")
async def startup_event():
    if not URL:
        print("ERROR: RENDER_EXTERNAL_URL не задан!")
        return

    webhook_url = f"{URL}/telegram"
    
    # Отладочный вывод
    print(f"Попытка установки webhook на URL: {webhook_url}")
    
    await app_bot.bot.set_webhook(webhook_url)
    print("Webhook установлен!")




