from agents.agent import run_agent
from core.storage import storage
from loguru import logger

async def enqueue_task(user_id: str, task: str) -> str:
    job_id = f"job_{user_id}_{abs(hash(task)) % 1000000}"
    
    try:
        result = await run_agent(task, user_id)
        await storage.save_task(job_id, {
            "user_id": user_id,
            "task": task,
            "result": result,
            "result_preview": result[:500] + "..." if len(result) > 500 else result
        })
        logger.success(f"Задача {job_id} выполнена")
        return job_id
    except Exception as e:
        logger.error(f"Task failed: {e}")
        return job_id