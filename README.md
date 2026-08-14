# Support Communication Optimizer

Support Communication Optimizer is a lightweight demo that helps support analysts improve customer- or publisher-facing resolution messages. It detects problematic/banned wording, suggests terminology and tone improvements, and produces a side-by-side diff so analysts can see exactly what changed.

**Repository layout**
- `backend/` — FastAPI backend (Python). No database; configuration-driven banned-word rules and LLM integration.
- `frontend/` — Vite + React single-page app that posts analyst drafts to the backend and shows suggested edits and diffs.

**Security & Privacy**
- No user-pasted text is persisted by the application. Input is processed in-memory and sent to the configured LLM for a short-lived response. Do not paste confidential or regulated data into the demo.
- Do not commit secrets. Use the provided example env files: [backend/.env.example](backend/.env.example) and [frontend/.env.example](frontend/.env.example).

## 1. Architecture

- Frontend: React + Vite SPA. Configurable `VITE_API_BASE_URL` controls the API base for production builds.
- Backend: FastAPI REST API (`/api/analyze`, `/api/health`) with services for banned-word detection, LLM wrapping, validation, and diffing.
- LLM: Configurable via environment variable `GEMINI_API_KEY` and routed through the backend service wrapper.

## 2. Local development setup

Prerequisites:
- Python 3.11+ (Py 3.13 recommended per workspace)
- Node.js 18+ and npm

Backend (local dev):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Create backend/.env from backend/.env.example and fill GEMINI_API_KEY for local testing only
uvicorn app.main:app --app-dir backend/app --host 127.0.0.1 --port 8000
```

Notes:
- For development you may use `--reload` with `uvicorn` but do not enable that in production.

Frontend (local dev):

```bash
cd frontend
npm install
# Optionally create frontend/.env from frontend/.env.example
npm run dev
```

The frontend by default calls relative API paths (so a Vite proxy or running the frontend from the same origin works). To point the built frontend to a remote backend, set `VITE_API_BASE_URL` in the frontend environment.

## 3. Environment variables

Backend — required (configure in your deployment environment):

- `GEMINI_API_KEY` — API key for Gemini / Generative Language API. Do NOT commit this to source control.
- `ALLOWED_ORIGINS` — comma-separated list of allowed CORS origins (e.g. `http://localhost:5173,https://app.example.com`). Keep this restrictive in production.
- `RATE_LIMIT_MAX` (optional) — max requests per window (demo default 60).
- `RATE_LIMIT_WINDOW` (optional) — window in seconds for rate limiting (demo default 60).

Frontend — required for configuring production API base:

- `VITE_API_BASE_URL` — the absolute URL to the backend during production (e.g. `https://api.example.com`). If empty, the frontend uses relative paths to the current origin.

See the example env files: [backend/.env.example](backend/.env.example) and [frontend/.env.example](frontend/.env.example).

## 4. Frontend setup (production build)

To build the frontend for production:

```bash
cd frontend
# Set VITE_API_BASE_URL in the environment or create a .env with VITE_API_BASE_URL
npm run build
# Serve the `dist/` directory from a static file server or CDN
```

Important: Do not hardcode `localhost` addresses in production. Use `VITE_API_BASE_URL` so the built assets call the correct backend origin.

## 5. Backend setup (production)

Example production startup using `gunicorn` with Uvicorn workers (recommended for multiple workers):

```bash
# install gunicorn in your production environment
pip install gunicorn
# run with 4 workers, bind to 0.0.0.0:8000
gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 app.main:app
```

Or using `uvicorn` directly (single process):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Do NOT run the server with `--reload` in production; `--reload` is intended for development only.

Set the required environment variables (`GEMINI_API_KEY`, `ALLOWED_ORIGINS`) in your host or container runtime — do not store the real keys in source control.

## 6. Gemini API setup

1. Obtain a Gemini / Generative Language API key from your Google Cloud project or provider account.
2. Place the key into a secure secret store or as an environment variable in the runtime environment: `GEMINI_API_KEY=ya29...`.
3. Restart the backend process so the process environment includes the key.

The backend service will raise a safe error if the key is missing; the key is never returned to clients or written to logs.

## 7. Deployment instructions

- Build the frontend with `npm run build`, set `VITE_API_BASE_URL` to your backend URL during build time or serve the built assets and ensure the browser can reach the backend origin.
- Deploy the backend to a server or container with the `GEMINI_API_KEY` and `ALLOWED_ORIGINS` environment variables set.
- Use HTTPS for all production traffic and keep `ALLOWED_ORIGINS` restrictive.
- Add a production-grade rate limiter (Redis or API gateway) rather than the demo in-memory limiter.

## 8. Privacy behavior

- This application does not persist user-entered text to disk or a database. Text is forwarded to the configured LLM for processing and the returned result is sent back to the browser.
- Users must not paste sensitive or regulated information into the demo.

## 9. Security considerations

- Do not commit any secrets to source control. Use the provided example files to keep secrets local only: [backend/.env.example](backend/.env.example) and [frontend/.env.example](frontend/.env.example).
- Replace the in-memory rate limiter with a distributed rate limiter (Redis, API gateway) for production.
- Configure logging to avoid writing full request bodies or any secrets to logs.
- Use HTTPS and a reverse proxy or load balancer to terminate TLS.

## 10. Example input / output

Example input (an analyst draft):

```
Hi, your account violated policy 123. We will suspend you. Visit http://example.com for details.
```

Example output (improved_text):

```
Hello — thank you for contacting support. We identified an issue with your account related to Policy 123. To resolve this, please review the guidance at https://example.com and let us know if you need further assistance.
```

The response includes a `changes` array describing the exact edits (original → replacement) and a `diff` payload suitable for side-by-side or inline highlighting.

## 11. Troubleshooting & further work

- Add CI checks such as `pip-audit` and `npm audit` to detect vulnerable dependencies.
- Add automated secrets scanning in CI to prevent accidental commits of `.env` files.
- Swap the demo rate limiter for a production-grade solution.

If you'd like, I can add CI configuration, a Redis-backed rate limiter example, or a simple systemd unit / Dockerfile for deployment.
