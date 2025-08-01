FROM ghcr.io/astral-sh/uv:python3.10-bookworm
ENV PYTHONDONTWRITEBYTECODE 1
ENV UV_LINK_MODE=copy
WORKDIR /app
COPY ./backend/pyproject.toml ./backend/uv.lock /app/ 

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev
COPY ./backend /app/backend 
ENV PATH="/app/.venv/bin:$PATH"
