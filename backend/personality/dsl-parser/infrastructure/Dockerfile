# Build stage
FROM ocaml/opam:alpine-ocaml-5.1 AS builder

# Install system dependencies
USER root
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    pkgconfig \
    && apk add --no-cache \
    ca-certificates

# Switch to opam user for building
USER opam
WORKDIR /build

# Copy dependency files first for better caching
COPY --chown=opam:opam dune-project opam* ./
RUN opam install . --deps-only --with-test 2>/dev/null || \
    opam install dune menhir core

# Copy source and build
COPY --chown=opam:opam --exclude=infrastructure . .
RUN eval $(opam env) && dune build --profile release

# Production stage
FROM alpine:latest

# Install runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    && addgroup -S appuser \
    && adduser -S appuser -G appuser

WORKDIR /app

# Copy built binary
COPY --from=builder /build/_build/install/default/bin/* ./

# Set ownership
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ./main --health-check || exit 1

CMD ["./main"]
