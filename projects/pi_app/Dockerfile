FROM ghcr.io/astral-sh/uv:python3.10-bookworm
ENV PYTHONDONTWRITEBYTECODE 1
ENV UV_LINK_MODE=copy
COPY ./backend /backend 
WORKDIR /backend
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev
WORKDIR /
ENV PATH="/backend/.venv/bin:$PATH"