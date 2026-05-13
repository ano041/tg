import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from config import MODEL, SENTRY_DSN

def init_sentry():
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment="production",
            release="1.0.0",
            integrations=[AsyncioIntegration(), RedisIntegration()],
            traces_sample_rate=0.5,
            _experiments={"profiles_sample_rate": 0.2},
        )
        sentry_sdk.set_tag("model", MODEL)
