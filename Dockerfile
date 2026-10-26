# =========================================================================
# Stage 1: Build React + TypeScript + Vite frontend
# =========================================================================
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# =========================================================================
# Stage 2: Production Python runtime (non-root, minimal layer)
# =========================================================================
FROM python:3.13-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Create unprivileged runtime user
RUN useradd -m -u 1000 -s /bin/bash appuser

# Install production Python dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy application files with ownership set to appuser
COPY --chown=appuser:appuser backend/ ./backend/
COPY --from=frontend-builder --chown=appuser:appuser /app/frontend/dist ./frontend/dist

USER appuser

EXPOSE 8080

# Use exec to ensure uvicorn receives SIGTERM directly
CMD ["sh", "-c", "exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}"]
