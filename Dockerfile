# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast wheel building
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project definition
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Build wheel
RUN uv build --wheel --out-dir /dist

# Final minimal runtime image
FROM python:3.11-slim AS runtime

LABEL maintainer="KodeKloud Community"
LABEL description="KodeKloud Model Context Protocol (MCP) Server"

# Create non-root user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /home/appuser/app

# Install wheel from builder
COPY --from=builder /dist/*.whl ./
RUN pip install --no-cache-dir ./*.whl && rm -f ./*.whl

# Switch to unprivileged user
USER 10001:10001

# Expose HTTP/SSE port
EXPOSE 8000

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    KODEKLOUD_USE_MOCK=true \
    KODEKLOUD_MCP_TRANSPORT=stdio \
    KODEKLOUD_MCP_HOST=0.0.0.0 \
    KODEKLOUD_MCP_PORT=8000

# Default entrypoint runs the MCP CLI
ENTRYPOINT ["kodekloud-mcp"]
CMD ["--transport", "stdio"]
