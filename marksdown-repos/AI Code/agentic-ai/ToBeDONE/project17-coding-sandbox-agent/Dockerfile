# Runs the experiments and tests. Namespaces (Level 1) need privileges Docker does not give by default, so inside
# a plain container Level 1 reports "unavailable" and is skipped. That is the correct behaviour: ask, don't assume.
FROM python:3.12-slim
WORKDIR /app
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
RUN useradd -m app && chown -R app /app
USER app
CMD ["python", "-m", "pytest", "-q"]
