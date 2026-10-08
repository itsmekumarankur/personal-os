FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py bank.py tools.py guardrails.py store.py observability.py ratelimit.py llm.py agent.py main.py ./

# Run as a normal user, not root. /data holds the database and is the only place the app writes.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app \
 && mkdir -p /data && chown 10001:10001 /data
USER 10001

ENV DB_PATH=/data/platform.db
EXPOSE 8000

# One process on purpose: the database is SQLite (one writer) and the rate limiter is in memory.
# --factory builds the app from the environment at start-up (and stops with a clear error if it is wrong).
CMD ["uvicorn", "main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
