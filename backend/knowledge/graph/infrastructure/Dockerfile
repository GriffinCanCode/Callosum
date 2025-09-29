# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    git \
    && apk add --no-cache ca-certificates

# Install air for hot reloading (dev only)
RUN go install github.com/air-verse/air@latest

# Copy go mod files for dependency caching
COPY go.mod go.sum* ./
RUN go mod download

# Copy source (excluding infrastructure)
COPY --exclude=infrastructure . .

# Build optimized binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-w -s" -a -installsuffix cgo \
    -o graph-engine main.go

# Production stage
FROM alpine:latest

# Install runtime dependencies and create user
RUN apk --no-cache add \
    ca-certificates \
    tzdata \
    netcat-openbsd \
    && addgroup -S appuser \
    && adduser -S appuser -G appuser \
    && rm -rf /var/cache/apk/*

WORKDIR /app

# Copy binary and air from builder
COPY --from=builder /build/graph-engine .
COPY --from=builder /go/bin/air /usr/local/bin/
COPY --from=builder /build/infrastructure/.air.toml ./infrastructure/

# Set ownership
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD nc -z localhost 8002 || exit 1

CMD ["./graph-engine"]
