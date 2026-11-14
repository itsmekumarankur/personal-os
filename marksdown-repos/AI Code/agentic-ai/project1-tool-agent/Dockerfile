

# Use a lightweight Python 3.12 image as the base.
# "slim" = smaller image with fewer unnecessary packages.
FROM python:3.12-slim


# Inside the container, make /app the working directory.
# All following commands run from /app.
WORKDIR /app


# Copy dependency file from our machine into the container.
COPY requirements.txt .


# Install all Python dependencies required by the application.
# --no-cache-dir keeps the Docker image smaller.
RUN pip install --no-cache-dir -r requirements.txt


# Copy our application code into the container.
#
# agent.py -> AI agent / tool-calling logic
# main.py  -> application/server entry point
COPY agent.py main.py .


# Document that the application listens on port 8000.
# This does NOT actually publish the port to the host.
EXPOSE 8000


# Start the application when the container starts.
#
# uvicorn = ASGI server
# main:app = find the "app" object inside main.py
# --host 0.0.0.0 = accept connections from outside the container
# --port 8000 = application listens on port 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


# ------------------------------------------------------------
# FLOW:
#
# Dockerfile
#     |
#     v
# Python 3.12 environment
#     |
#     v
# Install dependencies
#     |
#     v
# Copy agent.py + main.py
#     |
#     v
# Start Uvicorn
#     |
#     v
# API running inside container :8000
# ------------------------------------------------------------