# Callosum Development with Docker

## Quick Start

```bash
# Start all services
npm run dev:docker

# Or manually
./infrastructure/dev.sh
```

## Services

| Service | Port | Language | Purpose |
|---------|------|----------|---------|
| ai-engine | 8000 | Python | AI/ML operations |
| dsl-parser | 8001 | OCaml | DSL compilation |
| graph-engine | 8002 | Go | Knowledge graphs |
| event-processor | 4000 | Elixir | Event streaming |
| postgres | 5432 | SQL | Primary database |
| redis | 6379 | Cache | Session/cache store |
| adminer | 8080 | PHP | Database admin |

## Commands

### Development Commands
```bash
# Start development environment (with cleanup)
npm run dev:docker

# Quick start (no cleanup, faster)
npm run dev:quick

# Stop all services
npm run dev:stop

# Restart all services
npm run dev:restart

# Rebuild all containers
npm run dev:rebuild

# View logs
npm run dev:logs

# Check service status
npm run dev:status
```

### Docker Management
```bash
# Build containers
npm run docker:build

# Start/stop services  
npm run docker:up
npm run docker:down

# Cleanup Commands
npm run docker:clean          # Gentle cleanup
npm run docker:clean-project  # Clean only Callosum
npm run docker:clean-all      # Remove everything (DANGEROUS)
npm run docker:reset          # Full reset with rebuild
```

## Development

All services are optimized for development:

### Hot Reloading
- **Python**: uvicorn auto-reload
- **OCaml**: dune watch mode  
- **Go**: air hot reloader
- **Elixir**: mix auto-compile

### Build Optimizations
- **Multi-stage builds**: Smaller final images
- **Layer caching**: Faster rebuilds
- **Build context**: Optimized with .dockerignore
- **Security**: Non-root users in production images
- **Health checks**: Built-in container health monitoring

## Database

PostgreSQL initializes with:
- Database: `callosum`
- User: `postgres` 
- Password: `postgres`
- Admin UI: http://localhost:8080

## Cleanup & Maintenance

### Automatic Cleanup
The development environment automatically cleans up:
- Stopped containers
- Dangling images  
- Unused networks
- Build cache

### Manual Cleanup
```bash
# Gentle cleanup (safe)
./infrastructure/cleanup.sh

# Project-only cleanup
./infrastructure/cleanup.sh project

# Full cleanup (removes data!)
./infrastructure/cleanup.sh project --with-volumes

# Weekly maintenance
./infrastructure/docker-maintenance.sh
```

## Troubleshooting

**Container won't start:**
```bash
npm run dev:logs
```

**Out of disk space:**
```bash
npm run docker:clean
```

**Complete reset:**
```bash
npm run docker:reset
```

**Connect to service:**
```bash
docker compose -f infrastructure/compose.yml exec [service-name] sh
```
