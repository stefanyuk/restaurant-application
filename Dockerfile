# ===================== PYTHON-BASE =========================
FROM python:3.10-alpine3.13 as python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR="/opt/poetry/cache"

ENV PATH="$POETRY_HOME/bin:$PATH"

# ===================== BUILDER-BASE =========================

FROM python-base as builder

RUN apk update \
    && apk add libffi-dev build-base curl gcc postgresql-dev python3-dev musl-dev

RUN curl -sSL https://install.python-poetry.org | python3

WORKDIR /app

COPY pyproject.toml /app

RUN poetry install --no-dev

# ===================== DEVELOPMENT-BASE =========================
FROM python-base as development

WORKDIR /app

RUN apk update \
    && apk add postgresql-dev

COPY --from=builder $POETRY_HOME $POETRY_HOME

COPY . /app

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "src.app:app", "--reload", "--host", "0.0.0.0", "--port", "8000" ]
