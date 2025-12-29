"""
Gemini API Service
Implements manual Function Calling flow and integrates academic search tools.
"""

import base64
import time
from typing import Any, Dict, List, Literal, Optional
from google import genai
from google.genai import types

from config import gemini_config, semantic_scholar_config
from prompts.system_prompt import get_system_prompt, Language
from services.semantic_scholar import get_semantic_scholar_service
from utils.logger import logger


# Error messages i18n
ERROR_MESSAGES = {
    "zh": {
        "empty_response": "抱歉，我暂时无法处理您的请求。请稍后重试。",
        "processing_done": "处理完成。",
        "processing_error": "处理请求时发生错误: {error}",
        "too_many_calls": "处理过程中函数调用次数过多，请简化您的问题后重试。",
    },
    "en": {
        "empty_response": "Sorry, I'm unable to process your request at the moment. Please try again later.",
        "processing_done": "Processing complete.",
        "processing_error": "An error occurred while processing your request: {error}",
        "too_many_calls": "Too many function calls during processing. Please simplify your question and try again.",
    }
}


def _get_error_message(key: str, language: str = "zh", **kwargs) -> str:
    """Get error message for the specified language"""
    messages = ERROR_MESSAGES.get(language, ERROR_MESSAGES["zh"])
    msg = messages.get(key, messages.get(key, key))
    return msg.format(**kwargs) if kwargs else msg


def _build_search_papers_function(language: str = "zh") -> dict:
    """构建论文搜索函数声明，使用配置中的参数"""
    if language == "en":
        return {
            "name": "search_academic_papers",
            "description": "Search for academic papers to verify the scientific basis of claims. Use English keywords for more comprehensive results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (English recommended), e.g., 'breakfast eggs health benefits' or 'gender differences cognitive abilities'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": f"Number of results to return, default {semantic_scholar_config.DEFAULT_SEARCH_LIMIT}, max {semantic_scholar_config.MAX_SEARCH_LIMIT}"
                    },
                    "year_range": {
                        "type": "string",
                        "description": "Year range, format 'YYYY-YYYY', e.g., '2018-2024'"
                    },
                    "fields_of_study": {
                        "type": "string",
                        "description": "Fields of study, e.g., 'Medicine', 'Psychology', 'Biology', 'Neuroscience'"
                    }
                },
                "required": ["query"]
            }
        }
    
    return {
        "name": "search_academic_papers",
        "description": "搜索学术论文以验证论断的科学依据。使用英文关键词搜索可获得更全面的结果。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询词（推荐使用英文），例如 'breakfast eggs health benefits' 或 'gender differences cognitive abilities'"
                },
                "limit": {
                    "type": "integer",
                    "description": f"返回结果数量，默认{semantic_scholar_config.DEFAULT_SEARCH_LIMIT}，最多{semantic_scholar_config.MAX_SEARCH_LIMIT}"
                },
                "year_range": {
                    "type": "string",
                    "description": "年份范围，格式为 'YYYY-YYYY'，例如 '2018-2024'"
                },
                "fields_of_study": {
                    "type": "string",
                    "description": "研究领域，如 'Medicine', 'Psychology', 'Biology', 'Neuroscience'"
                }
            },
            "required": ["query"]
        }
    }


class GeminiService:
    """Gemini API Service with manual Function Calling"""
    
    def __init__(self, api_key: str, semantic_scholar_api_key: Optional[str] = None):
        logger.debug("gemini", "Initializing Gemini service", {
            "model": gemini_config.MODEL_NAME,
            "thinking_level": gemini_config.THINKING_LEVEL,
            "max_function_calls": gemini_config.MAX_FUNCTION_CALLS,
            "auto_function_calling": gemini_config.AUTO_FUNCTION_CALLING,
        })
        
        self.client = genai.Client(api_key=api_key)
        self.model = gemini_config.MODEL_NAME
        self.max_function_calls = gemini_config.MAX_FUNCTION_CALLS
        self.semantic_scholar = get_semantic_scholar_service(semantic_scholar_api_key)
        
        logger.info("gemini", "Gemini service initialized")
    
    def _get_config(self, language: Language = "zh") -> types.GenerateContentConfig:
        """Get generation config with language-specific system prompt and tools"""
        tools = types.Tool(function_declarations=[_build_search_papers_function(language)])
        
        return types.GenerateContentConfig(
            tools=[tools],
            system_instruction=get_system_prompt(language),
            thinking_config=types.ThinkingConfig(thinking_level=gemini_config.THINKING_LEVEL),
            # Disable automatic function calling, handle manually
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=not gemini_config.AUTO_FUNCTION_CALLING
            )
        )
    
    async def _execute_function(self, function_call: Any) -> Dict[str, Any]:
        """Execute function call"""
        func_name = function_call.name
        args = dict(function_call.args) if function_call.args else {}
        
        logger.function_call("gemini", func_name, args)
        start_time = time.time()
        
        if func_name == "search_academic_papers":
            result = await self.semantic_scholar.search_papers(
                query=args.get("query", ""),
                limit=min(
                    args.get("limit", semantic_scholar_config.DEFAULT_SEARCH_LIMIT),
                    semantic_scholar_config.MAX_SEARCH_LIMIT
                ),
                year_range=args.get("year_range"),
                fields_of_study=args.get("fields_of_study")
            )
        else:
            logger.warning("gemini", f"Unknown function: {func_name}")
            result = {"error": f"Unknown function: {func_name}"}
        
        elapsed_ms = (time.time() - start_time) * 1000
        logger.function_result("gemini", func_name, {
            "elapsed_ms": f"{elapsed_ms:.2f}",
            "success": result.get("success", False) if isinstance(result, dict) else True,
            "papers_count": len(result.get("papers", [])) if isinstance(result, dict) else None,
        })
        
        return result
    
    def _build_contents(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        files: Optional[List[Dict[str, Any]]] = None
    ) -> List[types.Content]:
        """Build conversation contents"""
        contents = []
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "user")
                parts = []
                
                if "content" in msg:
                    parts.append(types.Part(text=msg["content"]))
                
                if "function_call" in msg:
                    fc = msg["function_call"]
                    parts.append(types.Part(
                        function_call=types.FunctionCall(
                            name=fc["name"],
                            args=fc["args"]
                        )
                    ))
                
                if "function_response" in msg:
                    fr = msg["function_response"]
                    parts.append(types.Part.from_function_response(
                        name=fr["name"],
                        response=fr["response"]
                    ))
                
                if parts:
                    contents.append(types.Content(role=role, parts=parts))
        
        # Build current user message
        user_parts = []
        
        # Add files (images/docs)
        if files:
            for file_info in files:
                mime_type = file_info.get("mime_type", "")
                data = file_info.get("data")  # base64 encoded
                
                if data:
                    file_bytes = base64.b64decode(data)
                    user_parts.append(types.Part.from_bytes(
                        data=file_bytes,
                        mime_type=mime_type
                    ))
        
        # Add text message
        if user_message:
            user_parts.append(types.Part(text=user_message))
        
        if user_parts:
            contents.append(types.Content(role="user", parts=user_parts))
        
        return contents
    
    async def chat(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        files: Optional[List[Dict[str, Any]]] = None,
        max_function_calls: Optional[int] = None,
        language: Language = "zh"
    ) -> Dict[str, Any]:
        """
        Process user message with support for multi-turn function calling.
        """
        max_calls = max_function_calls if max_function_calls is not None else self.max_function_calls
        config = self._get_config(language)
        
        logger.separator("gemini", "Starting Gemini API call")
        
        contents = self._build_contents(user_message, conversation_history, files)
        function_call_records = []
        
        for iteration in range(max_calls + 1):
            try:
                logger.debug("gemini", f"API call iteration {iteration + 1}/{max_calls + 1}")
                iter_start_time = time.time()
                
                # Call Gemini API
                logger.api_call_start("gemini", "generate_content", {
                    "model": self.model,
                    "contents_count": len(contents),
                    "language": language,
                })
                
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config
                )
                
                iter_elapsed_ms = (time.time() - iter_start_time) * 1000
                logger.api_call_end("gemini", "generate_content", True, {
                    "elapsed_ms": f"{iter_elapsed_ms:.2f}",
                    "candidates_count": len(response.candidates) if response.candidates else 0,
                })
                
                if not response.candidates or not response.candidates[0].content:
                    logger.warning("gemini", "API returned empty response")
                    return {
                        "response": _get_error_message("empty_response", language),
                        "thinking_summary": None,
                        "function_calls": function_call_records,
                        "updated_history": self._extract_history(contents)
                    }
                
                candidate = response.candidates[0]
                content = candidate.content
                # Check for function calls
                function_calls = []
                text_parts = []
                thinking_summary = None
                
                for part in content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append(part.function_call)
                    elif hasattr(part, 'text') and part.text:
                        if hasattr(part, 'thought') and part.thought:
                            thinking_summary = part.text
                        else:
                            text_parts.append(part.text)
                
                # Execute function calls if any
                if function_calls and iteration < max_calls:
                    logger.info("gemini", f"Executing {len(function_calls)} function calls")
                    
                    contents.append(content)
                    function_response_parts = []
                    
                    for fc in function_calls:
                        result = await self._execute_function(fc)
                        function_call_records.append({
                            "name": fc.name,
                            "args": dict(fc.args) if fc.args else {},
                            "result": result
                        })
                        
                        function_response_part = types.Part.from_function_response(
                            name=fc.name,
                            response={"result": result}
                        )
                        function_response_parts.append(function_response_part)
                    
                    contents.append(types.Content(
                        role="tool",
                        parts=function_response_parts
                    ))
                    
                    continue
                
                # Return final response
                final_response = "\n".join(text_parts) if text_parts else _get_error_message("processing_done", language)
                
                updated_history = self._extract_history(contents)
                updated_history.append({
                    "role": "model",
                    "content": final_response
                })
                
                logger.info("gemini", "Gemini API call complete")
                logger.separator("gemini", "Gemini API call ended")
                
                return {
                    "response": final_response,
                    "thinking_summary": thinking_summary,
                    "function_calls": function_call_records,
                    "updated_history": updated_history
                }
                
            except Exception as e:
                logger.error("gemini", f"API call exception: {str(e)}")
                error_msg = _get_error_message("processing_error", language, error=str(e))
                return {
                    "response": error_msg,
                    "thinking_summary": None,
                    "function_calls": function_call_records,
                    "updated_history": self._extract_history(contents),
                    "error": str(e)
                }
        
        logger.warning("gemini", f"Exceeded max function calls ({max_calls})")
        return {
            "response": _get_error_message("too_many_calls", language),
            "thinking_summary": None,
            "function_calls": function_call_records,
            "updated_history": self._extract_history(contents)
        }
    
    def _extract_history(self, contents: List[types.Content]) -> List[Dict[str, Any]]:
        """Extract conversation history from Content list"""
        history = []
        
        for content in contents:
            entry = {"role": content.role}
            
            for part in content.parts:
                if hasattr(part, 'text') and part.text:
                    entry["content"] = part.text
                elif hasattr(part, 'function_call') and part.function_call:
                    entry["function_call"] = {
                        "name": part.function_call.name,
                        "args": dict(part.function_call.args) if part.function_call.args else {}
                    }
                elif hasattr(part, 'function_response') and part.function_response:
                    entry["function_response"] = {
                        "name": part.function_response.name,
                        "response": part.function_response.response
                    }
            
            history.append(entry)
        
        return history


_gemini_service: Optional[GeminiService] = None


def get_gemini_service(
    api_key: str,
    semantic_scholar_api_key: Optional[str] = None
) -> GeminiService:
    """Get Gemini service instance"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService(api_key, semantic_scholar_api_key)
    return _gemini_service
