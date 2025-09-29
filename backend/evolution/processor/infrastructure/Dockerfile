# Build stage
FROM hexpm/elixir:1.15.6-erlang-26.0.2-alpine-3.18.2 AS builder

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    git \
    nodejs \
    npm \
    && apk add --no-cache \
    ca-certificates

WORKDIR /build

# Install hex and rebar
RUN mix local.hex --force && \
    mix local.rebar --force

# Set build environment
ENV MIX_ENV=prod

# Copy mix files for dependency caching
COPY mix.exs mix.lock* ./
RUN mix deps.get --only prod

# Copy source (excluding infrastructure)
COPY --exclude=infrastructure . .

# Compile and build release
RUN mix deps.compile && \
    mix compile && \
    mix release --overwrite

# Production stage
FROM alpine:latest

# Install runtime dependencies
RUN apk add --no-cache \
    ncurses-libs \
    openssl \
    ca-certificates \
    bash \
    netcat-openbsd \
    && addgroup -S appuser \
    && adduser -S appuser -G appuser

WORKDIR /app

# Copy release from builder
COPY --from=builder /build/_build/prod/rel/event_processor ./

# Set ownership
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 4000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD nc -z localhost 4000 || exit 1

CMD ["./bin/event_processor", "start"]
