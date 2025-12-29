# Truth Seeker

An AI-powered tool to verify life claims. It combines Gemini 3 Pro with Semantic Scholar academic search to help users debunk myths and find the truth.

## Features

- 🔍 **Claim Verification**: Input common life claims (health, psychology, etc.), and AI will judge their veracity.
- 📚 **Academic Support**: Automatically searches for relevant academic papers to provide evidence-based scientific explanations.
- 🖼️ **Multimodal Support**: Upload images and documents; AI will extract claims from them.
- 💬 **Interactive Chat**: Supports follow-up questions and challenges, with history stored locally in the browser.
- 📱 **Mobile Friendly**: Responsive design for a smooth experience on mobile devices.

## Tech Stack

### Backend
- **FastAPI** - Python Web Framework
- **google-genai** - Gemini API SDK
- **Semantic Scholar API** - Academic paper search
- **asyncio** - Asynchronous task queue (respecting 1 RPS limit)

### Frontend
- **Next.js 15** - React Framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **react-markdown** - Markdown rendering

## Project Structure

```
Truth Seeker/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment variables example
│   ├── Dockerfile           # Backend Dockerfile
│   ├── prompts/
│   │   └── system_prompt.py # System prompts
│   ├── routers/
│   │   └── chat.py          # Chat API routes
│   ├── services/
│   │   ├── gemini_service.py      # Gemini API service
│   │   └── semantic_scholar.py    # Academic search service
│   └── utils/
│       └── queue_manager.py # Request queue management
├── frontend/
│   ├── app/
│   │   ├── layout.tsx       # Root layout
│   │   ├── page.tsx         # Main page
│   │   └── globals.css      # Global styles
│   ├── components/
│   │   ├── ChatMessage.tsx  # Message components
│   │   ├── ChatInput.tsx    # Input components
│   │   └── ConversationSidebar.tsx  # Sidebar
│   ├── hooks/
│   │   └── useConversationHistory.ts  # History hook
│   ├── lib/
│   │   └── api.ts           # API client
│   ├── Dockerfile           # Frontend Dockerfile
│   └── package.json
├── nginx/
│   └── nginx.conf           # Nginx config
├── docker-compose.yml       # Docker compose
└── README.md
```

## Quick Start

### 1. Clone the project

```bash
git clone https://github.com/feixukeji/truth-seeker.git
cd truth-seeker
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env
# Edit .env and fill in your API keys:
# GOOGLE_API_KEY=Your Gemini API Key
# SEMANTIC_SCHOLAR_API_KEY=Your Semantic Scholar API Key (Optional)
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 4. Run Services

**Start Backend** (Port 8000):
```bash
cd backend
.\venv\Scripts\activate
python main.py
# Or use: uvicorn main:app --reload
```

**Start Frontend** (Port 3000):
```bash
cd frontend
npm run dev
```

### 5. Access Application

Open your browser and visit http://localhost:3000

## Production Deployment (Docker)

This project supports one-click containerized deployment using Docker Compose, including frontend, backend, and Nginx reverse proxy.

### 1. Prerequisites

Ensure your server has:
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### 2. Configure Environment Variables

Create a `.env` file in the `backend` directory and fill in your API keys:

```bash
cd backend
# Windows
copy .env.example .env
# Linux/Mac
# cp .env.example .env

# Edit .env and fill in real keys
```

### 3. Start Services

Run the following in the project root:

```bash
docker-compose up -d --build
```

### 4. Access Services

Once started, Nginx will listen on port 80.
- Access via server IP or domain: `http://localhost` or `http://your-server-ip`
- API endpoints are at: `http://your-server-ip/api`

### 5. Stop Services

```bash
docker-compose down
```

## Getting API Keys

### Gemini API
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Create or log in to your Google account
3. Click "Get API Key" to obtain your key

### Semantic Scholar API (Optional but Recommended)
1. Visit [Semantic Scholar API](https://www.semanticscholar.org/product/api)
2. Register for an API Key (initial limit 1 RPS)
3. You can use it without a key, but you will share the public rate limit

## Usage

1. **Input Claim**: Enter a life claim you want to verify, e.g., "Do eggs increase cholesterol?"

2. **Upload Files**: You can upload images or PDF files; AI will automatically extract claims for verification.

3. **View Results**: AI will provide a judgment (Correct / Partially Correct / Incorrect / Insufficient Evidence) along with:
   - A brief explanation
   - Detailed scientific analysis
   - Citations of relevant academic papers

4. **Continue Conversation**: Ask for details or challenge the judgment.

## Notes

- Semantic Scholar API is limited to 1 request/second; you may need to wait in a queue during high traffic.
- Gemini 3 Pro uses thinking capabilities; the first response may take some time.
- Conversation history is stored in the browser's `localStorage`; clearing browser data will lose history.

## License

This project is licensed under the [PolyForm Noncommercial License](LICENSE).