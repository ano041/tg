from core.storage import storage
from billing.plans import get_plan
from core.logging_config import logger

class SubscriptionManager:
    async def get_user_subscription(self, user_id):
        sub_data = await storage.get_subscription(user_id)
        if not sub_data:
            return {"plan_id": "free", "stripe_sub_id": None, "requests_used": 0}
        return sub_data

    async def set_user_subscription(self, user_id, plan_id, stripe_sub_id=None):
        await storage.save_subscription(user_id, {
            "plan_id": plan_id,
            "stripe_sub_id": stripe_sub_id,
            "requests_used": 0
        })

    async def check_access(self, user_id):
        sub = await self.get_user_subscription(user_id)
        plan = get_plan(sub["plan_id"])
        if plan.requests_per_month and sub["requests_used"] >= plan.requests_per_month:
            logger.warning(f"User {user_id} exceeded request limit")
            return False
        return True

    async def increment_usage(self, user_id):
        await storage.increment_usage(user_id)

    async def get_plan_for_user(self, user_id):
        sub = await self.get_user_subscription(user_id)
        return get_plan(sub["plan_id"])

subscription_manager = SubscriptionManager()