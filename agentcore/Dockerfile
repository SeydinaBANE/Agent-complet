FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

FROM python:3.12-slim AS production

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

EXPOSE 8000
CMD ["uvicorn", "agentcore.main:app", "--host", "0.0.0.0", "--port", "8000"]
