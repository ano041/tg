import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from loguru import logger

from core.task_queue import enqueue_task
from core.rate_limiter import limiter
from core.abuse_protection import is_admin, is_message_too_long, contains_spam, is_system_command
from core.feedback import store_feedback
from core.storage import storage
from billing.stripe_client import create_checkout_session
from billing.subscription import subscription_manager
from billing.plans import PLANS

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    if is_system_command(text):
        await update.message.reply_text("Используйте /help для списка команд.")
        return
    if is_message_too_long(text):
        await update.message.reply_text("Сообщение слишком длинное.")
        return
    if contains_spam(text) and not is_admin(user_id):
        await update.message.reply_text("Сообщение выглядит как спам.")
        return
    if not is_admin(user_id) and not limiter.is_allowed(user_id):
        await update.message.reply_text("Превышен лимит запросов. Подождите немного.")
        return

    try:
        job_id = await enqueue_task(user_id, text)
        await update.message.reply_text(f"✅ Задача принята!\nID: `{job_id}`\nАгент начал работу...")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Не удалось обработать запрос.")

# Команды (можно расширить)
async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Функция подписки в разработке.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Статус: Активен ✅")

def run_telegram_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("status", status_command))
    
    logger.info("🤖 Telegram бот запущен")
    app.run_polling()