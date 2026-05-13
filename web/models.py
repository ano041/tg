from pydantic import BaseModel, Field
from typing import Optional, List

class TaskOut(BaseModel):
    job_id: str
    user_id: str
    task: str
    status: str
    result_preview: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

class StatsOut(BaseModel):
    total: int
    completed: int
    failed: int
    in_progress: int

class AdminUserAction(BaseModel):
    user_id: str
    action: str = Field(..., pattern="^(block|unblock)$")