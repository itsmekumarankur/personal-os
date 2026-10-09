FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./
RUN useradd --system --uid 10001 app
USER app
# one image, three roles:  python serve.py auth | mcp | a2a
ENTRYPOINT ["python", "serve.py"]
