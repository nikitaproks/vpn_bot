FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_VERSION=1.6.1
ENV POETRY_VENV=/opt/poetry-venv

# Install poetry separated from system interpreter
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

COPY . /app/telegram
WORKDIR /app/telegram

# Set the environment variable to include the shared directory in PYTHONPATH
ENV PYTHONPATH="/app/shared:${PYTHONPATH}"

RUN poetry install --no-interaction --no-ansi
