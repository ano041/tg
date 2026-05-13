import json
import datetime
from typing import Optional, List
from core.task_queue import get_redis_pool
from core.logging_config import logger

class TaskRecord:
    def __init__(self, job_id, user_id, task, status, result=None, created_at=None, completed_at=None):
        self.job_id = job_id
        self.user_id = user_id
        self.task = task
        self.status = status
        self.result = result
        self.created_at = created_at or datetime.datetime.utcnow().isoformat()
        self.completed_at = completed_at

    def to_dict(self):
        return {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "task": self.task[:200] + "..." if len(self.task) > 200 else self.task,
            "status": self.status,
            "result_preview": (self.result[:300] + "...") if self.result else None,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }

class TaskStorage:
    REDIS_KEY_PREFIX = "task:"
    INDEX_KEY = "task_index"
    SUBSCRIPTION_KEY_PREFIX = "sub:"
    IMPROVEMENTS_KEY = "pending_improvements"

    def __init__(self):
        self.pool = None

    async def _get_pool(self):
        if self.pool is None:
            self.pool = await get_redis_pool()
        return self.pool

    async def save_task(self, record: TaskRecord):
        pool = await self._get_pool()
        key = self.REDIS_KEY_PREFIX + record.job_id
        await pool.set(key, json.dumps(record.to_dict()))
        await pool.sadd(self.INDEX_KEY, record.job_id)

    async def get_task(self, job_id):
        pool = await self._get_pool()
        data = await pool.get(self.REDIS_KEY_PREFIX + job_id)
        if data:
            return json.loads(data)
        return None

    async def list_tasks(self, limit=50, user_id=None):
        pool = await self._get_pool()
        job_ids = await pool.smembers(self.INDEX_KEY)
        tasks = []
        for jid in list(job_ids)[-limit*2:]:
            task = await self.get_task(jid)
            if task:
                if user_id and task["user_id"] != user_id:
                    continue
                tasks.append(task)
        tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return tasks[:limit]

    async def update_task_status(self, job_id, status, result=None):
        pool = await self._get_pool()
        key = self.REDIS_KEY_PREFIX + job_id
        data = await pool.get(key)
        if data:
            record = json.loads(data)
            record["status"] = status
            if result:
                record["result_preview"] = result[:300]
            record["completed_at"] = datetime.datetime.utcnow().isoformat()
            await pool.set(key, json.dumps(record))

    async def get_stats(self):
        pool = await self._get_pool()
        job_ids = await pool.smembers(self.INDEX_KEY)
        total = len(job_ids)
        completed = failed = in_progress = 0
        for jid in job_ids:
            task = await self.get_task(jid)
            if task:
                if task["status"] == "complete": completed += 1
                elif task["status"] == "failed": failed += 1
                else: in_progress += 1
        return {"total": total, "completed": completed, "failed": failed, "in_progress": in_progress}

    async def save_subscription(self, user_id, data):
        pool = await self._get_pool()
        await pool.set(self.SUBSCRIPTION_KEY_PREFIX + user_id, json.dumps(data))

    async def get_subscription(self, user_id):
        pool = await self._get_pool()
        data = await pool.get(self.SUBSCRIPTION_KEY_PREFIX + user_id)
        if data:
            return json.loads(data)
        return None

    async def increment_usage(self, user_id):
        pool = await self._get_pool()
        key = self.SUBSCRIPTION_KEY_PREFIX + user_id
        data = await pool.get(key)
        if data:
            record = json.loads(data)
            record["requests_used"] = record.get("requests_used", 0) + 1
            await pool.set(key, json.dumps(record))

    async def save_pending_improvements(self, suggestions):
        pool = await self._get_pool()
        await pool.set(self.IMPROVEMENTS_KEY, json.dumps(suggestions))

    async def get_pending_improvements(self):
        pool = await self._get_pool()
        data = await pool.get(self.IMPROVEMENTS_KEY)
        if data:
            return json.loads(data)
        return {}

storage = TaskStorage()