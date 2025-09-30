# AI Language Personality DSL Compiler
# Build stage for Callosum personality compiler
FROM ocaml/opam:alpine-ocaml-5.1 AS builder

# Install system dependencies for OCaml compilation
USER root
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    pkgconfig \
    && apk add --no-cache \
    ca-certificates

# Switch to opam user for building DSL compiler
USER opam
WORKDIR /build

# Copy dependency files first for better Docker layer caching
COPY --chown=opam:opam dune-project opam* ./
RUN opam install . --deps-only --with-test 2>/dev/null || \
    opam install dune menhir core

# Copy AI personality DSL source and build
COPY --chown=opam:opam --exclude=infrastructure . .
RUN eval $(opam env) && dune build --profile release

# Production stage - AI personality compiler service
FROM alpine:latest

# Install runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    && addgroup -S personality \
    && adduser -S personality -G personality

WORKDIR /app

# Copy compiled AI personality DSL tools
COPY --from=builder /build/_build/install/default/bin/* ./

# Set ownership for personality service user
RUN chown -R personality:personality /app
USER personality

EXPOSE 8001

# Health check for AI personality compiler service
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ./dsl-parser --version || exit 1

# Run AI personality compiler
CMD ["./dsl-parser"]
