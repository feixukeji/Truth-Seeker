"""
Truth Seeker - Backend Entry Point
FastAPI application providing claim verification API
"""

import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import (
    api_keys, gemini_config, queue_config, 
    server_config, app_info, debug_config
)
from routers.chat import router as chat_router, process_chat_task
from utils.queue_manager import queue_manager
from utils.logger import logger

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    queue_manager.set_processor(process_chat_task)
    await queue_manager.start_worker()
    
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    print("🚀 Truth Seeker service started")
    print(f"📚 Model: {gemini_config.MODEL_NAME}")
    print(f"🔬 Semantic Scholar API: {'Configured' if api_keys.SEMANTIC_SCHOLAR_API_KEY else 'Not configured (using public limit)'}")
    
    if debug_config.DEBUG:
        print(f"🐛 DEBUG mode enabled (Level: {debug_config.LOG_LEVEL})")
        logger.info("main", "App startup complete", {
            "model": gemini_config.MODEL_NAME,
            "thinking_level": gemini_config.THINKING_LEVEL,
            "max_function_calls": gemini_config.MAX_FUNCTION_CALLS,
            "queue_max_size": queue_config.MAX_QUEUE_SIZE,
        })
    
    yield
    
    cleanup_task.cancel()
    await queue_manager.stop_worker()
    logger.info("main", "Service shutting down...")
    print("👋 Service stopped")


async def periodic_cleanup():
    """Periodically clean up old tasks"""
    while True:
        try:
            await asyncio.sleep(queue_config.CLEANUP_INTERVAL_SECONDS)
            queue_manager.cleanup_old_tasks(max_age_seconds=queue_config.TASK_MAX_AGE_SECONDS)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("main", f"Error during cleanup: {e}")


app = FastAPI(
    title=app_info.NAME,
    description=app_info.DESCRIPTION,
    version=app_info.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=server_config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/")
async def root():
    """Health check"""
    return {
        "name": app_info.NAME,
        "status": "running",
        "version": app_info.VERSION,
        "model": gemini_config.MODEL_NAME
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "queue_size": queue_manager.get_queue_size(),
        "google_api_configured": bool(api_keys.GOOGLE_API_KEY),
        "semantic_scholar_api_configured": bool(api_keys.SEMANTIC_SCHOLAR_API_KEY)
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=server_config.HOST,
        port=server_config.PORT,
        reload=server_config.RELOAD
    )
