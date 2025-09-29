# Infrastructure Organization

## Structure

```
/infrastructure/                  # Root infrastructure
├── compose.yml                  # Main Docker Compose config
├── compose.override.yml         # Development overrides
├── dev.sh                      # Development startup script
├── README-docker.md            # Docker documentation
└── scripts/
    └── init.sql                # Database initialization

/backend/*/infrastructure/       # Service-specific infrastructure
├── Dockerfile                  # Service container definition
└── [service-specific configs]  # e.g., .air.toml for Go
```

## Design Principles

1. **Separation of Concerns**: Infrastructure separated from application code
2. **Service Isolation**: Each service has its own infrastructure directory
3. **Centralized Orchestration**: Root infrastructure manages service coordination
4. **Minimal, Memorable Names**: Simple, one-word directory names
5. **Strong Organization**: Clear hierarchy reduces cognitive load

## Usage

All Docker commands are centralized through npm scripts:

```bash
npm run dev:docker     # Start all services
npm run docker:build   # Build containers
npm run docker:up      # Start services
npm run docker:down    # Stop services
npm run docker:logs    # View logs
npm run docker:reset   # Reset and rebuild
```

## Benefits

- **Reduced Tech Debt**: Clear separation prevents configuration drift
- **Easy Navigation**: Infrastructure files easy to locate
- **Scalable**: Pattern scales to additional services
- **Maintainable**: Clear ownership of infrastructure per service
