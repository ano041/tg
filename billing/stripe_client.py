import os
import stripe
from dotenv import load_dotenv
from core.logging_config import logger
from billing.plans import get_plan

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

async def create_checkout_session(user_id, plan_id, success_url, cancel_url):
    plan = get_plan(plan_id)
    if not plan.stripe_price_id:
        raise ValueError("Free plan cannot be purchased")
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
            metadata={"user_id": user_id, "plan_id": plan_id},
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session.url
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise

async def cancel_subscription(subscription_id):
    try:
        stripe.Subscription.delete(subscription_id)
        return True
    except stripe.error.StripeError as e:
        logger.error(f"Stripe cancel error: {e}")
        return False