# Support Communication Optimizer

Lightweight demo app to help support analysts improve publisher/customer-facing resolution messages.

Architecture:

- backend/: FastAPI Python backend (no DB). Loads banned word config and provides REST API.
- frontend/: Vite + React single-page app for pasting draft responses and showing suggested edits.

Run (development):

Backend:

1. Create a Python virtualenv and install requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

2. Run the server:

```bash
uvicorn app.main:app --reload --app-dir backend/app --host 127.0.0.1 --port 8000
```

Frontend:

1. From `frontend/` install deps and run Vite:

```bash
cd frontend
npm install
npm run dev
```

Notes:
- API keys (e.g. Gemini) must be set in backend environment variables. See `backend/.env.example`.
- No user-entered text is persisted.

Next step: implement LLM integration, banned-word scanning, validation, and diffing logic.
# upport-Communication-Optimizer
