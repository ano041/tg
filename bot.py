main.py  
  
```python  
import os  
import asyncio  
import threading  
from dotenv import load_dotenv  
from telegram import Update  
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler  
from core.task_queue import enqueue_task  
from core.rate_limiter import limiter  
from core.abuse_protection import is_admin, is_message_too_long, contains_spam, is_system_command  
from core.logging_config import logger  
from core.feedback import store_feedback  
from core.storage import storage  
from billing.stripe_client import create_checkout_session  
from billing.subscription import subscription_manager  
from billing.plans import PLANS  
import uvicorn  
  
load_dotenv()  
TOKEN = os.getenv("TELEGRAM_TOKEN")  
  
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    user_id = str(update.effective_user.id)  
    message_text = update.message.text  
    if is_system_command(message_text):  
        await update.message.reply_text("Это команда, а не задача. Используйте /help")  
        return  
    if is_message_too_long(message_text):  
        await update.message.reply_text("Сообщение слишком длинное.")  
        return  
    if contains_spam(message_text) and not is_admin(user_id):  
        await update.message.reply_text("Спам обнаружен.")  
        logger.warning(f"Spam from {user_id}")  
        return  
    if not is_admin(user_id) and not limiter.is_allowed(user_id):  
        await update.message.reply_text("Слишком много запросов. Подождите минуту.")  
        return  
    try:  
        job_id = await enqueue_task(user_id, message_text)  
        await update.message.reply_text(f"✅ Задача принята, ID: `{job_id}`")  
    except Exception as e:  
        logger.exception("Enqueue failed")  
        await update.message.reply_text("❌ Не удалось поставить задачу в очередь.")  
  
async def subscribe_command(update: Update, context):  
    user_id = str(update.effective_user.id)  
    plan_id = context.args[0] if context.args else "pro"  
    if plan_id not in PLANS or plan_id == "free":  
        await update.message.reply_text("Доступные планы: pro, enterprise. Пример: /subscribe pro")  
        return  
    try:  
        checkout_url = await create_checkout_session(user_id, plan_id, "https://example.com/success", "https://example.com/cancel")  
        await update.message.reply_text(f"Для подписки на {plan_id.capitalize()} план перейдите по ссылке:\n{checkout_url}")  
    except Exception as e:  
        logger.error(f"Subscribe error: {e}")  
        await update.message.reply_text("Ошибка при создании сессии оплаты.")  
  
async def status_command(update: Update, context):  
    user_id = str(update.effective_user.id)  
    sub = await subscription_manager.get_user_subscription(user_id)  
    plan = await subscription_manager.get_plan_for_user(user_id)  
    await update.message.reply_text(f"Ваш план: {plan.name}\nИспользовано запросов: {sub['requests_used']} / {plan.requests_per_month}")  
  
async def feedback_callback(update: Update, context):  
    query = update.callback_query  
    await query.answer()  
    data = query.data.split("|")  
    if len(data) == 3 and data[0] == "rate":  
        job_id = data[1]  
        rating = data[2]  
        task_info = await storage.get_task(job_id)  
        if task_info:  
            user_id = str(update.effective_user.id)  
            await store_feedback(user_id=user_id, task=task_info["task"], answer=task_info.get("result_preview", ""), rating=rating)  
            await query.edit_message_text(text=query.message.text + f"\n\nСпасибо за оценку!")  
        else:  
            await query.edit_message_text(text=query.message.text + "\n\nНе удалось сохранить оценку.")  
  
def run_telegram_bot():  
    app = ApplicationBuilder().token(TOKEN).build()  
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))  
    app.add_handler(CommandHandler("subscribe", subscribe_command))  
    app.add_handler(CommandHandler("status", status_command))  
    app.add_handler(CallbackQueryHandler(feedback_callback, pattern="^rate\\|"))  
    logger.info("Telegram bot started")  
    app.run_polling()  
  
def run_web():  
    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, log_level="info")  
  
if __name__ == "__main__":  
    web_thread = threading.Thread(target=run_web, daemon=True)  
    web_thread.start()  
    run_telegram_bot()  
```  
  