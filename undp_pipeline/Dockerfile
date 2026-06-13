FROM python:3.12-slim

WORKDIR /app

FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

CMD ["streamlit", "run", "app_gemini.py", "--server.address=0.0.0.0", "--server.port=8080"]