FROM python:3.12-slim

WORKDIR /demo

COPY requirements.txt .

RUN pip install uv

RUN uv venv

RUN uv pip install -r requirements.txt

COPY ./src/server.py .

COPY ./src/client.py .

EXPOSE 8000

CMD ["uv", "run", "server.py"]

