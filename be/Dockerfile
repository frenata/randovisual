FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.6.10 /uv /bin/uv

COPY randovisual /app/randovisual
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

WORKDIR /app

RUN uv sync

CMD uv run fastapi run randovisual/api/app.py
