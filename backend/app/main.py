from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import time
from typing import Dict, List
from app.routes.health import router as health_router
from app.routes.analyze import router as analyze_router
from app.routes.diagnose import router as diagnose_router

app = FastAPI(title="Support Communication Optimizer - Backend")

# Configure CORS from environment or default to localhost dev origin only
allowed = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [o.strip() for o in allowed.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health_router, prefix="/api")
app.include_router(analyze_router, prefix="/api")
app.include_router(diagnose_router, prefix="/api")


# Basic in-memory rate limiter (per-IP). This is a simple mitigation for demo purposes only.
# Production should use a robust external rate-limiter (Redis, API gateway).
_RATE_LIMIT_STORE: Dict[str, List[float]] = {}
_RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "60"))
_RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client = request.client.host if request.client else "unknown"
    now = time.time()
    times = _RATE_LIMIT_STORE.get(client, [])
    # remove old
    times = [t for t in times if t > now - _RATE_LIMIT_WINDOW]
    if len(times) >= _RATE_LIMIT_MAX:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
    times.append(now)
    _RATE_LIMIT_STORE[client] = times
    response = await call_next(request)
    return response


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log server-side if needed; do not expose internal details to clients.
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/ready")
def ready():
    return {"status": "ready"}
