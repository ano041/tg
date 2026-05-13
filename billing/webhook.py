from fastapi import APIRouter, Request, HTTPException
import stripe
from billing.stripe_client import STRIPE_WEBHOOK_SECRET
from billing.subscription import subscription_manager
from core.logging_config import logger

router = APIRouter(prefix="/api/billing/webhook", tags=["billing"])

@router.post("/")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(400, "Invalid payload or signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        plan_id = session["metadata"]["plan_id"]
        subscription_id = session.get("subscription")
        await subscription_manager.set_user_subscription(user_id, plan_id, subscription_id)
        logger.info(f"Subscription activated for user {user_id}")
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        user_id = subscription["metadata"].get("user_id")
        if user_id:
            await subscription_manager.set_user_subscription(user_id, "free")
            logger.info(f"Subscription cancelled for user {user_id}")
    return {"status": "success"}