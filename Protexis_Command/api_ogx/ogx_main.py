import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from core.logging.loggers import get_protocol_logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Protexis_Command.api_ogx.middleware.ogx_auth import add_ogx_auth_middleware
from Protexis_Command.api_ogx.routes import messages
from Protexis_Command.api_ogx.services.ogx_message_worker import get_message_worker

logger = get_protocol_logger()
worker_task: Optional[asyncio.Task] = None


async def initialize_worker():
    try:
        worker = await get_message_worker()
        app.state.message_worker = worker
        await worker.start()
        logger.info("Message worker started successfully")
    except Exception as e:
        logger.error(f"Failed to start message worker: {str(e)}")
        app.state.worker_error = str(e)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global worker_task
    worker_task = asyncio.create_task(initialize_worker())
    logger.info("Application startup complete")
    yield
    if worker_task:
        await worker_task
    if hasattr(app.state, "message_worker"):
        await app.state.message_worker.stop()


app = FastAPI(
    title="OGx API",
    description="Internal API for OGx message handling and protocol management",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_ogx_auth_middleware(app)

app.include_router(
    messages.router,
    prefix="/api/v1",
    tags=["messages"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
