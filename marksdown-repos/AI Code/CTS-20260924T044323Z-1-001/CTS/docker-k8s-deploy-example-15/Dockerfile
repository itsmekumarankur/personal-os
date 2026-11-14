FROM python:3.11-slim

WORKDIR /demo

COPY requirements.txt .

RUN pip install uv 
RUN uv venv
RUN uv pip install -r requirements.txt

COPY server.py .
COPY client-sse.py .

EXPOSE 8000

CMD ["uv", "run", "server.py"]