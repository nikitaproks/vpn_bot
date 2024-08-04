FROM python:3.12-slim-bullseye
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
COPY . .
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir -r requirements.lock
