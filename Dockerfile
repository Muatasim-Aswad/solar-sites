# syntax=docker/dockerfile:1
# Build the React static files.
FROM node:26.12.0-bookworm-slim@sha256:298992629d69bbd5b2b03ad57094d8e4fcb3a8eeb7c4e25d29de656519568913 AS frontend
WORKDIR /build/frontend
RUN npm install --global pnpm@12.11.2
COPY apps/frontend/package.json apps/frontend/pnpm-lock.yaml apps/frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY apps/frontend/ ./
RUN pnpm run build

# Install Python dependencies and the app into a portable virtual environment.
FROM python:3.14.7-slim-bookworm@sha256:82bc3c539b8813ada9d68c63b40158fa002f7f33de9bf3312a3dfdc0620dff56 AS backend
COPY --from=ghcr.io/astral-sh/uv:0.13.1@sha256:4a1f3666816dafadd20ceb71eac9a7d56d7ef30279f7d64048519ab901ada336 /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /build/backend
COPY apps/backend/pyproject.toml apps/backend/uv.lock ./
# Cache dependencies separately from application source changes.
RUN uv sync --locked --no-dev --no-install-project
COPY apps/backend/src ./src
RUN uv sync --locked --no-dev --no-editable

# Serve both apps as a non-root user, with persistent SQLite data in /data.
FROM python:3.14.7-slim-bookworm@sha256:82bc3c539b8813ada9d68c63b40158fa002f7f33de9bf3312a3dfdc0620dff56 AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/solar-sites.sqlite3 FRONTEND_PATH=/app/frontend
RUN groupadd --gid 10001 solar \
    && useradd --uid 10001 --gid solar --no-create-home --shell /usr/sbin/nologin solar \
    && mkdir /data && chown solar:solar /data
COPY --from=backend /opt/venv /opt/venv
COPY --from=frontend /build/frontend/dist /app/frontend
WORKDIR /app
USER 10001:10001
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/readyz', timeout=3).read()"]
# This app serves HTTP directly, so forwarded proxy headers are not trusted.
CMD ["uvicorn", "solar_sites.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
