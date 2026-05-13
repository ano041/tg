from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from core.storage import storage
from web.models import TaskOut, StatsOut

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("/", response_model=List[TaskOut])
async def list_tasks(user_id: Optional[str] = Query(None), limit: int = Query(50, le=100)):
    return await storage.list_tasks(limit=limit, user_id=user_id)

@router.get("/{job_id}", response_model=TaskOut)
async def get_task(job_id: str):
    task = await storage.get_task(job_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/stats/overview", response_model=StatsOut)
async def get_stats():
    return await storage.get_stats()