FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY equalexperts_dataeng_exercise ./equalexperts_dataeng_exercise
COPY tests ./tests
COPY warehouse.db ./warehouse.db
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN uv sync --locked

RUN chmod +x docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["--help"]
