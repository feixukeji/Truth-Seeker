"""
Chat API Router
Handles user messages and file uploads.
"""

import time
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import base64

from config import api_keys
from services.gemini_service import get_gemini_service
from utils.queue_manager import queue_manager, TaskStatus
from utils.logger import logger

router = APIRouter(prefix="/api", tags=["chat"])

# Language type
Language = Literal["zh", "en"]


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_history: Optional[List[Dict[str, Any]]] = None
    language: Language = "zh"


class ChatWithFilesRequest(BaseModel):
    """Chat request with files"""
    message: str
    conversation_history: Optional[List[Dict[str, Any]]] = None
    files: Optional[List[Dict[str, str]]] = None  # [{"mime_type": "...", "data": "base64..."}]
    language: Language = "zh"


class TaskResponse(BaseModel):
    """Task response model"""
    task_id: str
    status: str
    position: int
    message: str


class TaskResultResponse(BaseModel):
    """Task result response model"""
    task_id: str
    status: str
    result: Optional[str] = None  # Returns response text directly
    error: Optional[str] = None
    position: Optional[int] = None


async def process_chat_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Function to process chat tasks"""
    start_time = time.time()
    
    # Get language setting
    language = payload.get("language", "zh")
    
    logger.separator("chat", "Processing chat task")
    logger.debug("chat", "Task payload", {
        "message": payload.get("message", "")[:100] + "..." if len(payload.get("message", "")) > 100 else payload.get("message", ""),
        "has_history": payload.get("conversation_history") is not None,
        "history_length": len(payload.get("conversation_history") or []),
        "has_files": payload.get("files") is not None,
        "files_count": len(payload.get("files") or []),
        "language": language,
    })
    
    if not api_keys.GOOGLE_API_KEY:
        logger.error("chat", "GOOGLE_API_KEY not configured")
        raise ValueError("GOOGLE_API_KEY not configured")
    
    service = get_gemini_service(api_keys.GOOGLE_API_KEY, api_keys.SEMANTIC_SCHOLAR_API_KEY)
    
    logger.debug("chat", "Calling Gemini service...")
    result = await service.chat(
        user_message=payload.get("message", ""),
        conversation_history=payload.get("conversation_history"),
        files=payload.get("files"),
        language=language
    )
    
    elapsed_ms = (time.time() - start_time) * 1000
    logger.info("chat", f"Chat task processed", {
        "elapsed_ms": f"{elapsed_ms:.2f}",
        "function_calls_count": len(result.get("function_calls", [])),
        "has_thinking": result.get("thinking_summary") is not None,
        "response_length": len(result.get("response", "")),
    })
    logger.separator("chat", "Chat task finished")
    
    # Return only the response field to simplify results
    return result.get("response", "")


@router.post("/chat", response_model=TaskResponse)
async def submit_chat(request: ChatRequest):
    """
    Submit chat request to queue
    Returns task ID, frontend polls for results
    """
    import datetime
    logger.info("chat", f">>> /api/chat request started @ {datetime.datetime.now().isoformat()}")
    
    logger.request_received("chat", "/api/chat", {
        "message_preview": request.message[:50] + "..." if len(request.message) > 50 else request.message,
        "has_history": request.conversation_history is not None,
        "language": request.language,
    })
    
    payload = {
        "message": request.message,
        "conversation_history": request.conversation_history,
        "files": None,
        "language": request.language
    }
    
    task = await queue_manager.submit_task(payload)
    
    logger.debug("chat", f"Task submitted to queue", {
        "task_id": task.id,
        "position": task.position,
        "queue_size": queue_manager.get_queue_size(),
    })
    
    return TaskResponse(
        task_id=task.id,
        status=task.status.value,
        position=task.position,
        message="Request added to queue"
    )


@router.post("/chat-with-files", response_model=TaskResponse)
async def submit_chat_with_files(request: ChatWithFilesRequest):
    """
    Submit chat request with files to queue
    """
    logger.request_received("chat", "/api/chat-with-files", {
        "message_preview": request.message[:50] + "..." if len(request.message) > 50 else request.message,
        "files_count": len(request.files) if request.files else 0,
        "language": request.language,
    })
    
    payload = {
        "message": request.message,
        "conversation_history": request.conversation_history,
        "files": request.files,
        "language": request.language
    }
    
    task = await queue_manager.submit_task(payload)
    
    logger.debug("chat", f"Task with files submitted to queue", {
        "task_id": task.id,
        "position": task.position,
    })
    
    return TaskResponse(
        task_id=task.id,
        status=task.status.value,
        position=task.position,
        message="Request added to queue"
    )


@router.post("/upload", response_model=TaskResponse)
async def upload_and_chat(
    message: str = Form(...),
    language: Language = Form("zh"),
    conversation_history: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[])
):
    """
    Upload files and submit chat request
    Supports images (JPEG, PNG, WEBP, HEIC, HEIF) and documents (PDF, TXT, Markdown, HTML, XML)
    """
    import json
    
    logger.request_received("chat", "/api/upload", {
        "message_preview": message[:50] + "..." if len(message) > 50 else message,
        "files_count": len(files),
        "file_names": [f.filename for f in files],
        "language": language,
    })
    
    # Parse conversation history
    history = None
    if conversation_history:
        try:
            history = json.loads(conversation_history)
            logger.debug("chat", f"Parsed conversation history, {len(history)} messages")
        except json.JSONDecodeError:
            logger.warning("chat", "Failed to parse conversation history JSON")
            history = None
    
    # Process uploaded files
    file_data = []
    allowed_types = {
        # Image types
        "image/jpeg", "image/png", "image/webp", "image/heic", "image/heif",
        # Document types
        "application/pdf",
        "text/plain",           # TXT
        "text/markdown",        # Markdown
        "text/x-markdown",      # Markdown (fallback)
        "text/html",            # HTML
        "text/xml",             # XML
        "application/xml",      # XML (fallback)
    }
    
    for file in files:
        logger.debug("chat", f"Processing uploaded file: {file.filename}", {
            "content_type": file.content_type,
        })
        
        if file.content_type not in allowed_types:
            logger.warning("chat", f"Unsupported file type: {file.content_type}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Supported: JPEG, PNG, WEBP, HEIC, PDF, TXT, Markdown, HTML, XML"
            )
        
        # Read file content and convert to base64
        content = await file.read()
        encoded = base64.b64encode(content).decode("utf-8")
        
        logger.debug("chat", f"File encoded: {file.filename}", {
            "original_size": len(content),
            "encoded_size": len(encoded),
        })
        
        file_data.append({
            "mime_type": file.content_type,
            "data": encoded,
            "filename": file.filename
        })
    
    # Submit task
    payload = {
        "message": message,
        "language": language,
        "conversation_history": history,
        "files": file_data if file_data else None
    }
    
    task = await queue_manager.submit_task(payload)
    
    logger.debug("chat", f"Upload task submitted to queue", {
        "task_id": task.id,
        "position": task.position,
        "files_processed": len(file_data),
    })
    
    return TaskResponse(
        task_id=task.id,
        status=task.status.value,
        position=task.position,
        message="Request added to queue"
    )


@router.get("/task/{task_id}", response_model=TaskResultResponse)
async def get_task_result(task_id: str):
    """
    Get task result
    Frontend should poll this endpoint until task is completed
    """
    task = queue_manager.get_task(task_id)
    
    if not task:
        logger.debug("chat", f"Task not found: {task_id[:8]}...")
        raise HTTPException(status_code=404, detail="Task not found")
    
    response = TaskResultResponse(
        task_id=task.id,
        status=task.status.value
    )
    
    if task.status == TaskStatus.COMPLETED:
        response.result = task.result
        # Log details for debugging
        result_info = {
            "has_result": task.result is not None,
            "result_type": type(task.result).__name__ if task.result else None,
        }
        if task.result and isinstance(task.result, dict):
            result_info["has_response"] = "response" in task.result
            result_info["response_length"] = len(task.result.get("response", "")) if task.result.get("response") else 0
        logger.debug("chat", f"Task completed: {task_id[:8]}...", result_info)
    elif task.status == TaskStatus.FAILED:
        response.error = task.error
        logger.debug("chat", f"Task failed: {task_id[:8]}...", {"error": task.error})
    else:
        response.position = task.position
        # Only log when position is low to avoid excessive logs
        if task.position <= 3:
            logger.debug("chat", f"Task waiting: {task_id[:8]}...", {"position": task.position})
    
    return response


@router.get("/queue/status")
async def get_queue_status():
    """Get current queue status"""
    return {
        "queue_size": queue_manager.get_queue_size(),
        "message": f"There are {queue_manager.get_queue_size()} pending requests in the queue"
    }


@router.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """Delete a completed task"""
    task = queue_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        raise HTTPException(status_code=400, detail="Only completed or failed tasks can be deleted")
    
    queue_manager.remove_task(task_id)
    
    return {"message": "Task deleted"}
