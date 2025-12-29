"""
Truth Seeker - Configuration
Centralized management of all adjustable parameters
"""

import os
from typing import Literal
from dotenv import load_dotenv

load_dotenv()


# ============== API Keys ==============
class APIKeys:
    """API Key configuration"""
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    SEMANTIC_SCHOLAR_API_KEY: str = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")


# ============== Gemini Model ==============
class GeminiConfig:
    """Gemini API configuration"""
    MODEL_NAME: str = "gemini-3-pro-preview"
    
    # Thinking level: "minimal", "low", "medium", "high"
    THINKING_LEVEL: Literal["minimal", "low", "medium", "high"] = "high"
    
    # Max function calls per conversation
    MAX_FUNCTION_CALLS: int = 20
    
    # Whether to enable automatic function calling (False = manual handling)
    AUTO_FUNCTION_CALLING: bool = False


# ============== Semantic Scholar ==============
class SemanticScholarConfig:
    """Semantic Scholar API configuration"""
    BASE_URL: str = "https://api.semanticscholar.org/graph/v1"
    
    # Rate limit (requests per second)
    RATE_LIMIT_RPS: float = 1.0
    
    # Request timeout in seconds
    REQUEST_TIMEOUT: float = 30.0
    
    # Default number of search results
    DEFAULT_SEARCH_LIMIT: int = 10
    
    # Max number of search results
    MAX_SEARCH_LIMIT: int = 50
    
    # Paper fields to return
    PAPER_FIELDS: str = "title,authors,tldr,abstract,year,venue,influentialCitationCount,citationCount"
    
    # Max authors to display
    MAX_AUTHORS_DISPLAY: int = 3


# ============== Task Queue ==============
class QueueConfig:
    """Task queue configuration"""
    MAX_QUEUE_SIZE: int = 100
    
    # Max task age in seconds
    TASK_MAX_AGE_SECONDS: int = 3600  # 1 hour
    
    # Cleanup interval in seconds
    CLEANUP_INTERVAL_SECONDS: int = 3600  # 1 hour
    
    # Worker loop timeout in seconds
    WORKER_TIMEOUT: float = 1.0


# ============== Server ==============
class ServerConfig:
    """Server configuration"""
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Enable hot reload
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"
    
    # Allowed CORS origins
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Add extra CORS origins from environment variables
    _extra_origins = os.getenv("CORS_ORIGINS", "")
    if _extra_origins:
        # Support comma or semicolon separated values
        separators = [",", ";"]
        for sep in separators:
            if sep in _extra_origins:
                CORS_ORIGINS.extend(_extra_origins.split(sep))
                break
        else:
            # If no separator, add directly
            if _extra_origins:
                CORS_ORIGINS.extend([_extra_origins])


# ============== Debug ==============
class DebugConfig:
    """Debug configuration"""
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    
    # Log level: DEBUG, INFO, WARNING, ERROR
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG" if DEBUG else "INFO")
    
    # Whether to output detailed request/response data
    VERBOSE_OUTPUT: bool = os.getenv("VERBOSE_OUTPUT", "true").lower() in ("true", "1", "yes") if DEBUG else False
    
    SHOW_TIMESTAMP: bool = True
    COLOR_OUTPUT: bool = True


# ============== App Info ==============
class AppInfo:
    """Basic application information"""
    NAME: str = "Truth Seeker API"
    DESCRIPTION: str = "AI-powered tool to verify life claims and debunk myths"
    VERSION: str = "1.0.0"


# Convenience access
api_keys = APIKeys()
gemini_config = GeminiConfig()
semantic_scholar_config = SemanticScholarConfig()
queue_config = QueueConfig()
server_config = ServerConfig()
debug_config = DebugConfig()
app_info = AppInfo()
