"""FastAPI main application for EventPilot AI.

Provides API routes for plan generation, budget recalculation, timeline recalculation,
health checks, and securely serves compiled static frontend assets with security headers.
"""

from contextlib import asynccontextmanager
import logging
from pathlib import Path
from typing import Set

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .schemas import (
    EventCreateRequest,
    FullPlanResponse,
    RecalculateRequest,
    RecalculateResponse,
    TimelineRecalculateRequest,
)
from .budget_engine import calculate_budget, scale_budget_items_for_guests
from .timeline_engine import generate_timeline, get_current_ist_date, parse_iso_date, TimelineResult
from .rate_limiter import InMemoryRateLimiter
from .gemini_client import generate_plan_with_gemini_or_fallback, get_auth_mode

# Structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("eventpilot.api")

rate_limiter = InMemoryRateLimiter(
    requests_per_minute=settings.rate_limit_per_minute,
    global_per_minute=settings.rate_limit_global_per_minute,
    trusted_proxy_hops=settings.trusted_proxy_hops,
    max_keys=10_000,
    window_seconds=60.0
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    auth_mode, project, location = get_auth_mode()
    logger.info("Starting EventPilot AI backend on port %d...", settings.port)
    logger.info("Environment: %s", settings.environment)
    logger.info("Auth mode chosen: %s (Project: %s, Location: %s)", auth_mode, project, location)
    logger.info("Gemini model: %s, Timeout: %.1fs", settings.gemini_model, settings.gemini_timeout_seconds)
    logger.info("Allowed CORS origins: %s", settings.allowed_cors_origins)
    yield
    logger.info("Shutting down EventPilot AI backend.")


app = FastAPI(
    title="EventPilot AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan
)

# 1. CORS middleware: fail-closed, no credentials, Content-Type header only
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


# 2. Security Headers & Request Body Size Limit Middleware
@app.middleware("http")
async def security_and_size_middleware(request: Request, call_next):
    # Enforce request body size limit
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > settings.max_body_bytes:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request payload exceeds maximum allowed size (1MB)."}
                )
        except ValueError:
            pass

    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"

    # Immutable caching for static assets
    if request.url.path.startswith("/assets/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"

    return response


# 3. Global exception handler for safe generic client errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error processing %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing your request. Please try again."}
    )


# 4. Healthcheck: returns strictly {"status": "ok"}
@app.get("/healthz", tags=["System"])
async def healthz():
    return {"status": "ok"}


# 5. Plan Generation (synchronous def to run in threadpool, keeping event loop responsive)
@app.post("/api/plans/generate", response_model=FullPlanResponse, tags=["Plans"])
def generate_plan(event: EventCreateRequest, request: Request):
    rate_limiter.check_rate_limit(request)

    # Validate that event date is not in the past
    today_ist = get_current_ist_date()
    if event.event_date < today_ist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Event date cannot be in the past ({event.event_date.isoformat()}). Please choose today or a future date."
        )

    return generate_plan_with_gemini_or_fallback(event)


# 6. Budget Recalculation
@app.post("/api/plans/recalculate", response_model=RecalculateResponse, tags=["Budget"])
async def recalculate_budget(payload: RecalculateRequest):
    items = payload.items
    changed_items = []
    review_items = []

    if payload.previous_guest_count is not None and payload.previous_guest_count != payload.guest_count:
        try:
            items, changed_items, review_items = scale_budget_items_for_guests(
                items=items,
                old_guest_count=payload.previous_guest_count,
                new_guest_count=payload.guest_count
            )
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    try:
        calc_result = calculate_budget(total_budget=payload.total_budget, items=items)
        return RecalculateResponse(
            budget=calc_result,
            changed_items=changed_items,
            review_items=review_items
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


# 7. Timeline Recalculation (Refreshes milestones and flags against current IST date)
@app.post("/api/plans/timeline", response_model=TimelineResult, tags=["Timeline"])
async def recalculate_timeline(payload: TimelineRecalculateRequest):
    try:
        completed_set = frozenset(payload.completed_ids)
        return generate_timeline(
            event_date_input=payload.event_date,
            event_type=payload.event_type,
            completed_ids=completed_set
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


# 8. Path-traversal safe SPA static file serving
DIST = (Path(__file__).resolve().parent.parent.parent / "frontend" / "dist").resolve()

if DIST.exists() and DIST.is_dir():
    assets_dir = DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API route not found")

        candidate = (DIST / full_path).resolve()
        if candidate.is_relative_to(DIST) and candidate.is_file():
            return FileResponse(candidate)

        # Fallback to index.html with no-cache header
        index_file = DIST / "index.html"
        return FileResponse(index_file, headers={"Cache-Control": "no-cache"})
