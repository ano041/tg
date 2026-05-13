from fastapi import APIRouter, Depends, HTTPException
from typing import Set
from web.auth import verify_admin
from web.models import AdminUserAction
from core.logging_config import logger

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(verify_admin)])

blocked_users: Set[str] = set()

@router.post("/users/action")
async def manage_user(action: AdminUserAction):
    if action.action == "block":
        blocked_users.add(action.user_id)
        logger.info(f"Admin blocked user {action.user_id}")
        return {"status": "blocked", "user_id": action.user_id}
    elif action.action == "unblock":
        blocked_users.discard(action.user_id)
        logger.info(f"Admin unblocked user {action.user_id}")
        return {"status": "unblocked", "user_id": action.user_id}
    raise HTTPException(400, "Invalid action")

@router.get("/blocked")
async def list_blocked():
    return {"blocked_users": list(blocked_users)}