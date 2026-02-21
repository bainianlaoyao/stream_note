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
cp .env.example .env
npm run dev
```

Access at http://localhost:5173

### Backend

```bash
cd stream-note-api
uv venv .venv
uv sync --python .venv/Scripts/python.exe
cp .env.example .env
uv run --python .venv/Scripts/python.exe python -m uvicorn app.main:app --reload
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

## Mobile Packaging (Vue + Capacitor)

From `stream-note-web/`:

```bash
# One-time setup (already committed in this repo)
npm install
npm run cap:add:android
npm run cap:add:ios

# Build web + sync native assets
npm run build:mobile

# Open native projects
npm run open:android
npm run open:ios
```

Set frontend API base URL in `stream-note-web/.env`:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Backend CORS origins are controlled by `CORS_ALLOW_ORIGINS` in `stream-note-api/.env`.

## One-Click Build & Deploy Script

Root script: `build-deploy.ps1`

It can:
- Build frontend `dist` and deploy to configured web root directory
- Build Android release packages (`.apk` + `.aab`)
- Build iOS `.ipa` on macOS (requires Xcode signing config)
- Start backend (`uvicorn`) on configured host/port
- Start frontend static server on configured host/port
- Automatically point frontend API to backend via `VITE_API_BASE_URL`

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-deploy.ps1
```

Dry-run (print commands only):

```powershell
powershell -ExecutionPolicy Bypass -File .\build-deploy.ps1 -DryRun
```

Important config is centralized at the top of `build-deploy.ps1`:
- `BackendPublicHost` + `BackendPublicPort` (frontend API target)
- `BackendBindHost` + `BackendPort` (backend listen address)
- `FrontendBindHost` + `FrontendPort` (frontend static server address)
- `BackendDeployDir` (backend runtime directory)
- `FrontendDeployDir` (frontend static files directory)
- `FrontendPublicOrigin` (used in backend CORS)

## Configuration

Edit `stream-note-api/.env`:
- `DATABASE_URL`: DB connection string
- `SQLITE_TIMEOUT_SECONDS`: SQLite lock wait timeout in seconds (default 30)
- `OPENAI_PROVIDER`: `openai_compatible | openai | siliconflow | ollama`
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
