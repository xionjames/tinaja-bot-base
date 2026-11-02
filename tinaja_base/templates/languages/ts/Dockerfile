# first stage: install the Python host and the TypeScript plugin's packages
FROM node:24-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /bin/uv

# git fetches tinaja-bot-base and the tinaja package from their git source
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*

# uv downloads Python into /opt/python, which the final stage copies along with the virtual environment
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_INSTALL_DIR=/opt/python UV_PYTHON_PREFERENCE=only-managed

WORKDIR /code
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# install the locked packages, without dev ones, into plugin/node_modules
WORKDIR /code/plugin
COPY plugin/package.json plugin/package-lock.json ./
RUN npm ci --omit=dev

# second unnamed stage
FROM node:24-slim

# Create a non-root user
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --gid 1001 app

WORKDIR /code

COPY --from=builder --chown=app:app /opt/python /opt/python
COPY --from=builder --chown=app:app /code/.venv /code/.venv
COPY --chown=app:app bot.toml CONTEXT.md ./
COPY --chown=app:app plugin/ ./plugin/
COPY --from=builder --chown=app:app /code/plugin/node_modules ./plugin/node_modules

USER app

ENV PATH="/code/.venv/bin:$PATH"

# the token comes at runtime: docker run --env-file .env <image>
ENTRYPOINT [ "tinaja-bot", "run" ]
