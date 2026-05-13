# Legacy agent module - replaced by core/orchestrator.py
# This file is kept for backward compatibility

from core.orchestrator import run_agent as _run_agent

async def run_agent(task: str, user_id: str = None) -> str:
    """Legacy wrapper - use core.orchestrator.run_agent instead"""
    return await _run_agent(user_id or "unknown", task)