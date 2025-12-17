import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

TOKEN = os.environ["BOT_TOKEN"]
PORT  = int(os.environ.get("PORT", 8000))
URL   = os.environ["RENDER_EXTERNAL_URL"]  # Render сам подставит URL

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
    webhook_url = f"{URL}/telegram"
    await app_bot.bot.set_webhook(webhook_url)
