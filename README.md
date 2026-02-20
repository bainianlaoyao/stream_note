# Stream Note

A minimalist note-taking app with AI-powered task recognition.

## Project Structure

```
stream_note/
├── stream-note-web/          # Vue 3 frontend
│   ├── src/
│   │   ├── components/       # Vue components
│   │   ├── views/            # Page views
│   │   ├── stores/           # Pinia stores
│   │   ├── services/         # API client
│   │   ├── types/            # TypeScript types
│   │   └── assets/           # Styles
│   └── package.json
├── stream-note-api/          # FastAPI backend
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── models/           # SQLAlchemy models
│   │   └── services/         # Business logic
│   ├── requirements.txt
│   └── .env.example
├── STREAM_NOTE_PLANNING.md   # Product spec
├── STREAM_NOTE_STYLE_GUIDE.md # Design system
└── README.md
```

## Quick Start

### Frontend

```bash
cd stream-note-web
npm install
npm run dev
```

Access at http://localhost:5173

### Backend

```bash
cd stream-note-api
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

API available at http://localhost:8000

Windows one-click start from project root (frontend + backend):

```powershell
.\start-dev.bat
```

Useful options:

```powershell
# Skip dependency installation for both services
.\start-dev.bat -NoInstall

# Custom ports
.\start-dev.bat -BackendPort 8001 -FrontendPort 5174
```

## Configuration

Edit `stream-note-api/.env`:
- `DATABASE_URL`: DB connection string
- `SQLITE_TIMEOUT_SECONDS`: SQLite lock wait timeout in seconds (default 30)
- `OPENAI_API_BASE`: Your OpenAI compatible endpoint
- `OPENAI_API_KEY`: API key  
- `OPENAI_MODEL`: Model name (e.g., llama3.2, gpt-4)
- `OPENAI_TIMEOUT_SECONDS`: Request timeout for LLM calls (default 20)
- `OPENAI_MAX_ATTEMPTS`: Retry attempts for transient LLM errors (default 2)
- `OPENAI_DISABLE_THINKING`: Disable model thinking/reasoning mode (`1` to disable, default `1`)

## Features

- Stream Editor with TipTap
- Tasks view with AI recognition
- Auto-save
- Backlink navigation
- Glassmorphism UI

## Developer Docs

- Frontend code knowledge: `docs/frontend-code-knowledge.md`
- Backend code knowledge: `docs/backend-code-knowledge.md`
