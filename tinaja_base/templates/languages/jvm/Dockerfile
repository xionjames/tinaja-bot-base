# first stage: build the plugin and its start script
FROM gradle:9.8.2-jdk21 AS plugin
WORKDIR /plugin
COPY plugin/ ./
RUN gradle installDist --no-daemon

# second stage: install the Python host
FROM eclipse-temurin:21-jre AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /bin/uv

# git is needed to fetch tinaja-bot-base from its git source
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# uv downloads Python into /opt/python, which the final stage copies along with the virtual environment
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_INSTALL_DIR=/opt/python UV_PYTHON_PREFERENCE=only-managed

WORKDIR /code
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# third unnamed stage: a Java runtime for the plugin, Python for the host
FROM eclipse-temurin:21-jre

# Create a non-root user
RUN groupadd --system --gid 1001 app && \
    useradd --system --uid 1001 --gid 1001 app

WORKDIR /code

COPY --from=builder --chown=app:app /opt/python /opt/python
COPY --from=builder --chown=app:app /code/.venv /code/.venv
COPY --chown=app:app bot.toml CONTEXT.md ./
COPY --from=plugin --chown=app:app /plugin/build/install/plugin ./plugin/build/install/plugin

USER app

ENV PATH="/code/.venv/bin:$PATH"

# the token comes at runtime: docker run --env-file .env <image>
ENTRYPOINT [ "tinaja-bot", "run" ]
