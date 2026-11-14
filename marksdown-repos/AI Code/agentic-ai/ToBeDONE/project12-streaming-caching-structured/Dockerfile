FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./
RUN useradd --system --uid 10001 app
USER app
EXPOSE 8000
# Streaming behind a proxy: set idle/read timeout above your longest silence and DISABLE response buffering.
CMD ["uvicorn", "server:app_factory", "--factory", "--host", "0.0.0.0", "--port", "8000"]
