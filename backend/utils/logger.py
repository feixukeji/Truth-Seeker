"""
Logger Utility Module
Provides unified debugging logs with color support.
"""

import json
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class LogLevel(Enum):
    """Log levels"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40


class Colors:
    """ANSI color codes"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"


class Logger:
    """Unified logging utility"""
    
    LEVEL_STYLES = {
        LogLevel.DEBUG: (Colors.CYAN, "🔍"),
        LogLevel.INFO: (Colors.GREEN, "ℹ️"),
        LogLevel.WARNING: (Colors.YELLOW, "⚠️"),
        LogLevel.ERROR: (Colors.RED, "❌"),
    }
    
    MODULE_COLORS = {
        "main": Colors.BRIGHT_MAGENTA,
        "chat": Colors.BRIGHT_BLUE,
        "gemini": Colors.BRIGHT_GREEN,
        "semantic_scholar": Colors.BRIGHT_CYAN,
        "queue": Colors.BRIGHT_YELLOW,
    }
    
    def __init__(self):
        self._config = None
        self._min_level = LogLevel.DEBUG
    
    @property
    def config(self):
        if self._config is None:
            from config import debug_config
            self._config = debug_config
            level_map = {
                "DEBUG": LogLevel.DEBUG,
                "INFO": LogLevel.INFO,
                "WARNING": LogLevel.WARNING,
                "ERROR": LogLevel.ERROR,
            }
            self._min_level = level_map.get(self._config.LOG_LEVEL.upper(), LogLevel.DEBUG)
        return self._config
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if log level should be output"""
        return self.config.DEBUG and level.value >= self._min_level.value
    
    def _format_timestamp(self) -> str:
        """Format timestamp"""
        if self.config.SHOW_TIMESTAMP:
            return datetime.now().strftime("%H:%M:%S.%f")[:-3]
        return ""
    
    def _colorize(self, text: str, color: str) -> str:
        """Add color to text"""
        if self.config.COLOR_OUTPUT:
            return f"{color}{text}{Colors.RESET}"
        return text
    
    def _format_data(self, data: Any, indent: int = 2) -> str:
        """Format data as readable string"""
        if data is None:
            return "None"
        
        try:
            if isinstance(data, (dict, list)):
                return json.dumps(data, ensure_ascii=False, indent=indent, default=str)
            return str(data)
        except Exception:
            return str(data)
    
    def _truncate(self, text: str, max_length: int = 500) -> str:
        """Truncate long text"""
        if len(text) > max_length:
            return text[:max_length] + f"... (truncated, total {len(text)} chars)"
        return text
    
    def _log(
        self,
        level: LogLevel,
        module: str,
        message: str,
        data: Optional[Any] = None,
        truncate_data: bool = True
    ):
        """Output log"""
        if not self._should_log(level):
            return
        
        color, icon = self.LEVEL_STYLES[level]
        module_color = self.MODULE_COLORS.get(module, Colors.WHITE)
        
        # Build log line
        parts = []
        
        # Timestamp
        timestamp = self._format_timestamp()
        if timestamp:
            parts.append(self._colorize(f"[{timestamp}]", Colors.DIM))
        
        # Level and icon
        level_str = f"{icon} {level.name:7}"
        parts.append(self._colorize(level_str, color))
        
        # Module name
        module_str = f"[{module}]"
        parts.append(self._colorize(module_str, module_color))
        
        # Message
        parts.append(message)
        
        # Output main line
        print(" ".join(parts), file=sys.stderr)
        
        # Output additional data
        if data is not None and self.config.VERBOSE_OUTPUT:
            formatted = self._format_data(data)
            if truncate_data:
                formatted = self._truncate(formatted, 1000)
            # Indent data
            indented = "\n".join(f"    {line}" for line in formatted.split("\n"))
            print(self._colorize(indented, Colors.DIM), file=sys.stderr)
    
    def debug(self, module: str, message: str, data: Optional[Any] = None, **kwargs):
        """Debug log"""
        self._log(LogLevel.DEBUG, module, message, data, **kwargs)
    
    def info(self, module: str, message: str, data: Optional[Any] = None, **kwargs):
        """Info log"""
        self._log(LogLevel.INFO, module, message, data, **kwargs)
    
    def warning(self, module: str, message: str, data: Optional[Any] = None, **kwargs):
        """Warning log"""
        self._log(LogLevel.WARNING, module, message, data, **kwargs)
    
    def error(self, module: str, message: str, data: Optional[Any] = None, **kwargs):
        """Error log"""
        self._log(LogLevel.ERROR, module, message, data, **kwargs)
    
    # ===== Helper methods for specific scenarios =====
    
    def request_received(self, module: str, endpoint: str, data: Optional[Any] = None):
        """Log received request"""
        self.info(module, f"📥 Request received: {endpoint}", data)
    
    def request_completed(self, module: str, endpoint: str, duration_ms: Optional[float] = None):
        """Log request completion"""
        msg = f"📤 Request completed: {endpoint}"
        if duration_ms is not None:
            msg += f" ({duration_ms:.2f}ms)"
        self.info(module, msg)
    
    def api_call_start(self, module: str, api_name: str, params: Optional[Any] = None):
        """Log API call start"""
        self.debug(module, f"🚀 API call start: {api_name}", params)
    
    def api_call_end(self, module: str, api_name: str, success: bool, result: Optional[Any] = None):
        """Log API call end"""
        status = "✅ Success" if success else "❌ Failed"
        self.debug(module, f"{status} API call: {api_name}", result)
    
    def function_call(self, module: str, func_name: str, args: Optional[Any] = None):
        """Log function call"""
        self.debug(module, f"🔧 Function call: {func_name}", args)
    
    def function_result(self, module: str, func_name: str, result: Optional[Any] = None):
        """Log function result"""
        self.debug(module, f"📋 Function result: {func_name}", result)
    
    def task_status(self, module: str, task_id: str, status: str, details: Optional[str] = None):
        """Log task status change"""
        msg = f"📌 Task [{task_id[:8]}...] status: {status}"
        if details:
            msg += f" - {details}"
        self.debug(module, msg)
    
    def separator(self, module: str, title: str = ""):
        """Output separator line"""
        if not self._should_log(LogLevel.DEBUG):
            return
        line = "─" * 50
        if title:
            print(self._colorize(f"──── {title} {line}", Colors.DIM), file=sys.stderr)
        else:
            print(self._colorize(line, Colors.DIM), file=sys.stderr)


# Global logger instance
logger = Logger()

