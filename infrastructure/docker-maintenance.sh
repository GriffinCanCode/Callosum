#!/bin/bash
# Docker maintenance script for Callosum
# Run this weekly to keep Docker clean and efficient

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🔧 Weekly Docker Maintenance${NC}"

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Docker is not running${NC}"
    exit 1
fi

# Show current usage
echo -e "${BLUE}📊 Before cleanup:${NC}"
docker system df

# Stop development services
echo -e "${BLUE}🛑 Stopping development services...${NC}"
docker compose -f infrastructure/compose.yml down 2>/dev/null || true

# Clean up containers
echo -e "${BLUE}📦 Removing stopped containers...${NC}"
docker container prune -f

# Clean up images (keep recent ones)
echo -e "${BLUE}🖼️  Removing dangling images...${NC}"
docker image prune -f

# Clean up networks
echo -e "${BLUE}🌐 Removing unused networks...${NC}"
docker network prune -f

# Clean up build cache (keep recent)
echo -e "${BLUE}🏗️  Cleaning build cache...${NC}"
docker builder prune -f --keep-storage 2GB

# Clean up volumes (be careful)
echo -e "${BLUE}💾 Checking volumes...${NC}"
unused_volumes=$(docker volume ls -qf dangling=true)
if [ -n "$unused_volumes" ]; then
    echo -e "${YELLOW}⚠️  Found unused volumes: $unused_volumes${NC}"
    read -p "Remove unused volumes? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
fi

# Show results
echo -e "${GREEN}✨ Maintenance complete!${NC}"
echo -e "${BLUE}📊 After cleanup:${NC}"
docker system df

# Restart development if it was running
if [ -f "/tmp/callosum_was_running" ]; then
    echo -e "${BLUE}🚀 Restarting development environment...${NC}"
    ./infrastructure/dev.sh quick
    rm /tmp/callosum_was_running
fi

echo -e "${GREEN}🎉 Docker maintenance complete!${NC}"
