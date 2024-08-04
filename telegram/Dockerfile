FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r requirements.lock
