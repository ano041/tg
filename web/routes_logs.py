from fastapi import APIRouter, Query, Depends
from web.auth import verify_admin
import aiofiles
import os

router = APIRouter(prefix="/api/logs", tags=["logs"], dependencies=[Depends(verify_admin)])
LOG_PATH = os.path.join("data", "logs", "agent.log")

@router.get("/")
async def get_logs(lines: int = Query(100, le=1000)):
    if not os.path.exists(LOG_PATH):
        return {"lines": []}
    async with aiofiles.open(LOG_PATH, "r", encoding="utf-8") as f:
        content = await f.readlines()
        return {"lines": [line.rstrip() for line in content[-lines:]]}