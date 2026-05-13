from dataclasses import dataclass
from typing import Optional

@dataclass
class Plan:
    id: str
    name: str
    price_usd: float
    requests_per_month: int
    max_message_length: int
    browser_automation: bool
    priority_queue: bool
    stripe_price_id: Optional[str] = None

PLANS = {
    "free": Plan(
        id="free", name="Free", price_usd=0.0,
        requests_per_month=100, max_message_length=2000,
        browser_automation=False, priority_queue=False
    ),
    "pro": Plan(
        id="pro", name="Pro", price_usd=9.99,
        requests_per_month=1000, max_message_length=4000,
        browser_automation=True, priority_queue=True,
        stripe_price_id="price_1234567890"
    ),
    "enterprise": Plan(
        id="enterprise", name="Enterprise", price_usd=49.99,
        requests_per_month=10000, max_message_length=8000,
        browser_automation=True, priority_queue=True,
        stripe_price_id="price_0987654321"
    )
}

def get_plan(plan_id):
    return PLANS.get(plan_id, PLANS["free"])