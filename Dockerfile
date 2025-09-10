FROM ghcr.io/astral-sh/uv:python3.13-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y netcat-openbsd curl && rm -rf /var/lib/apt/lists/*

RUN curl -L https://foundry.paradigm.xyz | bash

ENV PATH="/root/.foundry/bin:${PATH}"
RUN foundryup

COPY .env .env
COPY run.py run.py
COPY bot/ bot/
COPY pyproject.toml pyproject.toml

CMD sh -c "\
    anvil --host 0.0.0.0 --port 8545 & \
    until nc -z 127.0.0.1 8545; do echo '⏳ Waiting for anvil...'; sleep 1; done && \
    echo '✅ Anvil ready' && \
    uv sync && uv run run.py"
