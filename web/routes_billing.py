from fastapi import APIRouter
from billing.subscription import subscription_manager
from billing.plans import PLANS

router = APIRouter(prefix="/api/billing", tags=["billing"])

@router.get("/subscription/{user_id}")
async def get_user_subscription(user_id: str):
    sub = await subscription_manager.get_user_subscription(user_id)
    plan = await subscription_manager.get_plan_for_user(user_id)
    return {
        "user_id": user_id,
        "plan": plan.id,
        "plan_name": plan.name,
        "requests_used": sub["requests_used"],
        "requests_limit": plan.requests_per_month,
        "features": {
            "browser_automation": plan.browser_automation,
            "max_message_length": plan.max_message_length,
            "priority_queue": plan.priority_queue
        }
    }

@router.get("/plans")
async def list_plans():
    return {pid: {"name": p.name, "price_usd": p.price_usd, "requests": p.requests_per_month} for pid, p in PLANS.items()}