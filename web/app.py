from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from web.routes_tasks import router as tasks_router
from web.routes_admin import router as admin_router
from web.routes_logs import router as logs_router
from web.routes_billing import router as billing_router
from web.routes_improvements import router as improvements_router
from billing.webhook import router as webhook_router
from mcp.registry import mcp_registry
from config import MCP_SERVERS
from core.logging_config import logger
import asyncio as aio

app = FastAPI(title="AI Agent Web Panel", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(tasks_router)
app.include_router(admin_router)
app.include_router(logs_router)
app.include_router(billing_router)
app.include_router(improvements_router)
app.include_router(webhook_router)

@app.on_event("startup")
async def startup_event():
    await mcp_registry.load_servers(MCP_SERVERS)

    async def periodic():
        while True:
            await aio.sleep(3600)
            try:
                from agents.self_improver import maybe_improve_prompts
                await maybe_improve_prompts()
            except Exception as e:
                logger.error(f"Self-improvement error: {e}")
    aio.create_task(periodic())

@app.on_event("shutdown")
async def shutdown_event():
    await mcp_registry.shutdown()

@app.get("/health")
async def health():
    return {"status": "ok"}