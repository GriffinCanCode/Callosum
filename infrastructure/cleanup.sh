#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Docker Cleanup for Callosum${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop${NC}"
    exit 1
fi

# Function to get Docker disk usage
show_usage() {
    echo -e "${BLUE}📊 Current Docker disk usage:${NC}"
    docker system df
    echo ""
}

# Function for aggressive cleanup
aggressive_cleanup() {
    echo -e "${YELLOW}⚠️  Performing aggressive cleanup...${NC}"
    
    # Stop and remove all containers
    echo -e "${BLUE}🛑 Stopping all containers...${NC}"
    docker container stop $(docker container ls -aq) 2>/dev/null || true
    
    echo -e "${BLUE}🗑️  Removing all containers...${NC}"
    docker container rm $(docker container ls -aq) 2>/dev/null || true
    
    # Remove all images
    echo -e "${BLUE}🖼️  Removing all images...${NC}"
    docker image rm $(docker image ls -aq) 2>/dev/null || true
    
    # System prune with volumes
    echo -e "${BLUE}🧽 System prune with volumes...${NC}"
    docker system prune -af --volumes
}

# Function for gentle cleanup
gentle_cleanup() {
    echo -e "${GREEN}🧼 Performing gentle cleanup...${NC}"
    
    # Remove stopped containers
    echo -e "${BLUE}📦 Removing stopped containers...${NC}"
    docker container prune -f
    
    # Remove dangling images
    echo -e "${BLUE}🖼️  Removing dangling images...${NC}"
    docker image prune -f
    
    # Remove unused networks
    echo -e "${BLUE}🌐 Removing unused networks...${NC}"
    docker network prune -f
    
    # Remove build cache
    echo -e "${BLUE}🏗️  Removing build cache...${NC}"
    docker builder prune -f
}

# Function for project-specific cleanup
project_cleanup() {
    echo -e "${GREEN}🏛️  Callosum project cleanup...${NC}"
    
    # Stop Callosum services
    echo -e "${BLUE}🛑 Stopping Callosum services...${NC}"
    docker compose down 2>/dev/null || true
    
    # Remove Callosum images
    echo -e "${BLUE}🖼️  Removing Callosum images...${NC}"
    docker images | grep callosum | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true
    
    # Remove volumes (optional - preserves data by default)
    if [[ "$1" == "--with-volumes" ]]; then
        echo -e "${YELLOW}⚠️  Removing volumes (this will delete your data!)...${NC}"
        docker compose down -v 2>/dev/null || true
    fi
    
    # Clean build cache
    docker builder prune -f --filter label=com.docker.image.label=callosum
}

# Parse arguments
case "${1:-gentle}" in
    "gentle"|"g")
        show_usage
        gentle_cleanup
        ;;
    "aggressive"|"a")
        show_usage
        read -p "⚠️  This will remove ALL Docker containers, images, and volumes. Continue? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            aggressive_cleanup
        else
            echo -e "${BLUE}💡 Cancelled. Use 'gentle' mode for safer cleanup.${NC}"
            exit 0
        fi
        ;;
    "project"|"p")
        show_usage
        project_cleanup $2
        ;;
    "help"|"h"|"-h"|"--help")
        echo -e "${BLUE}Usage:${NC}"
        echo -e "  ${GREEN}./cleanup.sh [MODE] [OPTIONS]${NC}"
        echo ""
        echo -e "${BLUE}Modes:${NC}"
        echo -e "  ${GREEN}gentle${NC}     (default) Remove stopped containers, dangling images, unused networks"
        echo -e "  ${GREEN}aggressive${NC}  Remove ALL containers, images, volumes (DANGEROUS)"
        echo -e "  ${GREEN}project${NC}     Remove only Callosum-related containers and images"
        echo ""
        echo -e "${BLUE}Options for project mode:${NC}"
        echo -e "  ${GREEN}--with-volumes${NC}  Also remove data volumes (will delete your data)"
        echo ""
        echo -e "${BLUE}Examples:${NC}"
        echo -e "  ${GREEN}./cleanup.sh${NC}                    # Gentle cleanup"
        echo -e "  ${GREEN}./cleanup.sh project${NC}            # Clean only Callosum"
        echo -e "  ${GREEN}./cleanup.sh project --with-volumes${NC}  # Clean Callosum + data"
        echo -e "  ${GREEN}./cleanup.sh aggressive${NC}         # Remove everything (DANGEROUS)"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Unknown mode: $1${NC}"
        echo -e "${BLUE}💡 Use './cleanup.sh help' for usage information${NC}"
        exit 1
        ;;
esac

echo ""
show_usage
echo -e "${GREEN}✨ Cleanup complete!${NC}"

# Show reclaimed space
echo -e "${BLUE}💾 Reclaimed space summary:${NC}"
docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}"
