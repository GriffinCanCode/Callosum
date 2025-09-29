#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default mode
MODE="${1:-start}"

# Function to clean up before start
cleanup_before_start() {
    echo -e "${BLUE}🧹 Cleaning up before start...${NC}"
    
    # Remove stopped containers
    docker container prune -f >/dev/null 2>&1 || true
    
    # Remove dangling images  
    docker image prune -f >/dev/null 2>&1 || true
    
    # Clean build cache
    docker builder prune -f >/dev/null 2>&1 || true
    
    echo -e "${GREEN}✅ Pre-start cleanup complete${NC}"
}

if [[ "$MODE" == "help" ]] || [[ "$MODE" == "-h" ]] || [[ "$MODE" == "--help" ]]; then
    echo -e "${BLUE}Callosum Development Environment${NC}"
    echo ""
    echo -e "${BLUE}Usage:${NC}"
    echo -e "  ${GREEN}./dev.sh [MODE]${NC}"
    echo ""
    echo -e "${BLUE}Modes:${NC}"
    echo -e "  ${GREEN}start${NC}    (default) Start development environment with cleanup"
    echo -e "  ${GREEN}quick${NC}    Start without cleanup (faster)"
    echo -e "  ${GREEN}stop${NC}     Stop all services"
    echo -e "  ${GREEN}restart${NC}  Stop and restart all services"
    echo -e "  ${GREEN}rebuild${NC}  Rebuild all containers and restart"
    echo -e "  ${GREEN}logs${NC}     Show logs for all services"
    echo -e "  ${GREEN}status${NC}   Show status of all services"
    echo ""
    exit 0
fi

case "$MODE" in
    "stop")
        echo -e "${BLUE}🛑 Stopping Callosum services...${NC}"
        docker compose down
        echo -e "${GREEN}✅ Services stopped${NC}"
        exit 0
        ;;
    "restart")
        echo -e "${BLUE}🔄 Restarting Callosum services...${NC}"
        docker compose down
        cleanup_before_start
        ;;
    "rebuild")
        echo -e "${BLUE}🏗️  Rebuilding Callosum services...${NC}"
        docker compose down
        docker compose build --no-cache
        ;;
    "logs")
        echo -e "${BLUE}📋 Showing service logs...${NC}"
        docker compose logs -f
        exit 0
        ;;
    "status")
        echo -e "${BLUE}📊 Service status:${NC}"
        docker compose ps
        exit 0
        ;;
    "quick")
        echo -e "${BLUE}⚡ Quick start (no cleanup)...${NC}"
        ;;
    "start"|*)
        echo -e "${BLUE}🏛️  Starting Callosum Development Environment${NC}"
        cleanup_before_start
        ;;
esac

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Docker is not running. Please start Docker Desktop${NC}"
    exit 1
fi

# Check if compose files exist
if [[ ! -f "compose.yml" ]]; then
    echo -e "${YELLOW}⚠️  compose.yml not found${NC}"
    exit 1
fi

# Build and start services
echo -e "${GREEN}📦 Building Docker containers...${NC}"
docker compose build

echo -e "${GREEN}🚀 Starting services...${NC}"
docker compose up -d

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check service health
echo -e "${GREEN}🏥 Checking service health...${NC}"
services=("postgres:5432" "redis:6379" "ai-engine:8000" "graph-engine:8002" "event-processor:4000")
for service in "${services[@]}"; do
    name=${service%:*}
    port=${service#*:}
    if docker compose exec -T ${name} nc -z localhost ${port} 2>/dev/null; then
        echo -e "${GREEN}✅ ${name} is ready${NC}"
    else
        echo -e "${YELLOW}⚠️  ${name} is not yet ready${NC}"
    fi
done

echo -e "${BLUE}🎯 Services available at:${NC}"
echo -e "  ${GREEN}AI Engine:${NC}       http://localhost:8000"
echo -e "  ${GREEN}DSL Parser:${NC}      http://localhost:8001"
echo -e "  ${GREEN}Graph Engine:${NC}    http://localhost:8002"
echo -e "  ${GREEN}Event Processor:${NC} http://localhost:4000"
echo -e "  ${GREEN}Database Admin:${NC}  http://localhost:8080"
echo -e "  ${GREEN}PostgreSQL:${NC}      localhost:5432"
echo -e "  ${GREEN}Redis:${NC}           localhost:6379"

echo -e "${BLUE}📋 Useful commands:${NC}"
echo -e "  ${GREEN}Stop services:${NC}     ./infrastructure/dev.sh stop"
echo -e "  ${GREEN}View logs:${NC}         ./infrastructure/dev.sh logs"
echo -e "  ${GREEN}Restart all:${NC}       ./infrastructure/dev.sh restart"
echo -e "  ${GREEN}Rebuild all:${NC}       ./infrastructure/dev.sh rebuild"
echo -e "  ${GREEN}Service status:${NC}    ./infrastructure/dev.sh status"
echo -e "  ${GREEN}Cleanup Docker:${NC}    ./infrastructure/cleanup.sh"
echo -e "  ${GREEN}Hard reset:${NC}        ./infrastructure/cleanup.sh project --with-volumes"

echo -e "${GREEN}🎉 Development environment is ready!${NC}"
echo -e "${BLUE}💡 Use './infrastructure/dev.sh help' for more options${NC}"
