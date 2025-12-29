# Copilot Instructions - Truth Seeker

## Project Overview
AI-powered claim verification tool using Gemini 3 Pro + Semantic Scholar API to verify everyday claims.

## Architecture

### Data Flow
```
User Input → Frontend (Next.js) → Backend API (FastAPI) → Queue Manager
                                                          ↓
Poll Results ← Task Status ← Gemini API (Manual Function Calling) → Semantic Scholar
```

### Core Components
- **`backend/config.py`**: Centralized configuration for all tunable parameters (model, rate limits, queue, etc.)
- **`backend/services/gemini_service.py`**: Gemini API wrapper with **manual Function Calling**
- **`backend/services/semantic_scholar.py`**: Academic paper search with enforced 1 RPS rate limit
- **`backend/prompts/system_prompt.py`**: LLM system prompts controlling conversation logic
- **`frontend/lib/api.ts`**: Task submission + polling mechanism

## Key Technical Decisions

### Gemini Function Calling (Manual Mode)
```python
# Disable automatic function calling, handle call loop manually
automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)

# Function response uses role="tool" (Gemini 3 spec)
contents.append(types.Content(role="tool", parts=[...]))
```

### Async Task Queue
Backend uses queue to process requests, frontend polls for results:
- `POST /api/chat` → returns `task_id`
- `GET /api/task/{task_id}` → poll until `status: completed`

### Rate Limiting
Semantic Scholar API is limited to 1 RPS, enforced via `_wait_for_rate_limit()`.

## Development Commands

```bash
# Backend
cd backend
python -m venv venv && .\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env  # Fill in API keys
python main.py  # Start http://localhost:8000

# Frontend
cd frontend
npm install
npm run dev  # Start http://localhost:3000
```

## Code Standards

### Configuration Management
All tunable parameters must be defined in `backend/config.py`, no hardcoding:
```python
from config import gemini_config, semantic_scholar_config
# Usage: gemini_config.MODEL_NAME, semantic_scholar_config.DEFAULT_SEARCH_LIMIT
```

### API Keys
Access via `config.api_keys`, not directly using `os.getenv()`:
```python
from config import api_keys
service = get_gemini_service(api_keys.GOOGLE_API_KEY, api_keys.SEMANTIC_SCHOLAR_API_KEY)
```

### Frontend-Backend Interaction
- Frontend sends `role: "user" | "model"`
- Backend Gemini API uses `role: "user" | "model" | "tool"`
- Files transferred as base64: `{ mime_type: string, data: string }`
- Language parameter: `language: "zh" | "en"` for switching UI and System Prompt

## Adding New Features

### Adding a New Function Tool
1. Add new function declaration alongside `_build_search_papers_function()` in `gemini_service.py`
2. Add execution logic in `_execute_function()`
3. Update `self.tools = types.Tool(function_declarations=[...])` list

## Notes
- Gemini 3 requires function responses to use `role="tool"`, SDK handles thought signature automatically
- Frontend uses localStorage to store conversation history, max 50 entries
- Backend queue tasks are auto-cleaned after 1 hour