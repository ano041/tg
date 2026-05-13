from fastapi import APIRouter, Depends
from web.auth import verify_admin
from core.storage import storage
from core.logging_config import logger

router = APIRouter(prefix="/api/improvements", tags=["improvements"], dependencies=[Depends(verify_admin)])

@router.get("/")
async def get_improvements():
    return await storage.get_pending_improvements()

@router.post("/apply")
async def apply_improvements(agent: str = None):
    suggestions = await storage.get_pending_improvements()
    if not suggestions:
        return {"status": "no suggestions"}
    for ag, sug in suggestions.items():
        if agent and ag != agent:
            continue
        logger.info(f"Applying improvement for {ag}: {sug['changes_summary']}")
        print(f"New prompt for {ag}: {sug['new_prompt']}")
    await storage.save_pending_improvements({})
    return {"status": "applied"}