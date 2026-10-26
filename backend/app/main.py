"""FastAPI main application for EventPilot AI.

Provides API routes for plan generation, recalculation, health checks,
and serves compiled static frontend assets for single-container Cloud Run deployment.
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .schemas import (
    EventCreateRequest,
    FullPlanResponse,
    RecalculateRequest,
    RecalculateResponse
)
from .budget_engine import calculate_budget, scale_budget_items_for_guests
from .timeline_engine import parse_iso_date, get_current_ist_date
from .rate_limiter import InMemoryRateLimiter
from .gemini_client import generate_plan_with_gemini_or_fallback

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("eventpilot.api")

rate_limiter = InMemoryRateLimiter(requests_per_minute=settings.rate_limit_per_minute)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting EventPilot AI backend on port %d...", settings.port)
    logger.info("CORS origins configured: %s", settings.cors_origins)
    logger.info("Using Gemini model: %s", settings.gemini_model)
    yield
    logger.info("Shutting down EventPilot AI backend.")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan
)

# 1. CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# 2. Request body size limit middleware
@app.middleware("http")
async def limit_request_size_middleware(request: Request, call_next):
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
    return await call_next(request)


# 3. Global exception handler for safe generic client errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers
        )
    logger.exception("Unhandled server error processing %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing your request. Please try again."}
    )


# 4. Healthcheck
@app.get("/healthz", tags=["System"])
async def healthz():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "gemini_model": settings.gemini_model,
        "gemini_configured": bool(settings.gemini_api_key or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    }


# 5. Plan Generation
@app.post("/api/plans/generate", response_model=FullPlanResponse, tags=["Plans"])
async def generate_plan(event: EventCreateRequest, request: Request):
    # Enforce rate limit
    rate_limiter.check_rate_limit(request)

    # Validate that event date is not in the past at creation
    try:
        ev_date = parse_iso_date(event.event_date)
        today_ist = get_current_ist_date()
        if ev_date < today_ist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Event date cannot be in the past ({event.event_date}). Please choose today or a future date."
            )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

    # Generate plan with Gemini or fallback
    try:
        plan = generate_plan_with_gemini_or_fallback(event)
        return plan
    except Exception as exc:
        logger.exception("Error generating plan: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate event plan. Please check inputs and try again."
        )


# 6. Budget & Guest Recalculation (No money math in frontend)
@app.post("/api/plans/recalculate", response_model=RecalculateResponse, tags=["Budget"])
async def recalculate_budget(payload: RecalculateRequest):
    items = payload.items
    changed_items = []

    # If guest count changed, scale only per-guest items
    if payload.previous_guest_count is not None and payload.previous_guest_count != payload.guest_count:
        try:
            items, changed_items = scale_budget_items_for_guests(
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
            changed_items=changed_items
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


# 7. Static file serving for single-container Cloud Run deployment
frontend_dist_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
)

if os.path.exists(frontend_dist_path):
    logger.info("Mounting built frontend static files from: %s", frontend_dist_path)
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Allow API routes through
        if full_path.startswith("api/") or full_path == "healthz" or full_path.startswith("docs"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API route not found")
        file_path = os.path.join(frontend_dist_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist_path, "index.html"))
