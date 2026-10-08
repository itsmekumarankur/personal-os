FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY llm.py memory_store.py agents.py main.py ./

ENV MEMORY_DIR=/data/memory
RUN mkdir -p /data/memory

EXPOSE 8000

# One worker on purpose: sessions live in this process, and memory files use an in-process lock.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
