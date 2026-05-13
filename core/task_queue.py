import os
import asyncio
import httpx
from arq import create_pool
from arq.connections import RedisSettings
from dotenv import load_dotenv
from core.storage import storage, TaskRecord
from core.logging_config import logger
from billing.subscription import subscription_manager

load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

redis_pool = None

async def get_redis_pool():
    global redis_pool
    if redis_pool is None:
        redis_pool = await create_pool(RedisSettings(host=REDIS_HOST))
    return redis_pool

async def enqueue_task(user_id, task):
    pool = await get_redis_pool()
    job = await pool.enqueue_job("process_task", user_id, task)
    return job.job_id

async def send_telegram_message(chat_id, text, job_id=None):
    async with httpx.AsyncClient() as client:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text[:4000],
            "parse_mode": "Markdown"
        }
        if job_id:
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👍", callback_data=f"rate|{job_id}|positive"),
                 InlineKeyboardButton("👎", callback_data=f"rate|{job_id}|negative")]
            ])
            payload["reply_markup"] = keyboard.to_dict()
        await client.post(url, json=payload)

async def process_task(ctx, user_id, task):
    from core.orchestrator import run_agent

    job_id = ctx.get("job_id", "unknown")
    record = TaskRecord(job_id=job_id, user_id=user_id, task=task, status="processing")
    await storage.save_task(record)

    if not await subscription_manager.check_access(user_id):
        await send_telegram_message(user_id, "Лимит запросов исчерпан или у вас нет доступа.")
        await storage.update_task_status(job_id, "failed", "Limit exceeded")
        return

    plan_check = await subscription_manager.get_plan_for_user(user_id)
    if not plan_check.browser_automation and "browse" in task.lower():
        await send_telegram_message(user_id, "Браузерная автоматизация недоступна на вашем тарифе.")
        await storage.update_task_status(job_id, "failed", "Browser automation not allowed")
        return

    try:
        result = await run_agent(user_id, task)
        await storage.update_task_status(job_id, "complete", result)
        await send_telegram_message(user_id, result, job_id)
        await subscription_manager.increment_usage(user_id)
    except Exception as e:
        logger.exception("Task failed")
        await storage.update_task_status(job_id, "failed", str(e))
        await send_telegram_message(user_id, f"Task failed: {str(e)}")

class WorkerSettings:
    functions = [process_task]
    redis_settings = RedisSettings(host=REDIS_HOST)