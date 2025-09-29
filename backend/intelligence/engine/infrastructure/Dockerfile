# Build stage
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Install Python dependencies
COPY requirements.txt* ./
RUN pip install --no-cache-dir --user -r requirements.txt 2>/dev/null || \
    pip install --no-cache-dir --user uvicorn fastapi

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Update PATH to include local packages
ENV PATH=/root/.local/bin:$PATH

# Copy source (excluding infrastructure)
COPY --exclude=infrastructure . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
