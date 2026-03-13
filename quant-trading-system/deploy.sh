#!/bin/bash
# Quick deployment script for Crypto AI Trading System
# Usage: chmod +x deploy.sh && ./deploy.sh

set -e

echo "🚀 Crypto AI Trading System - Quick Deploy"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker installed${NC}"
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Parse arguments
ENVIRONMENT=${1:-development}
REBUILD=${2:-false}

echo -e "\n${YELLOW}Deployment Settings:${NC}"
echo "Environment: $ENVIRONMENT"
echo "Rebuild Images: $REBUILD"

# Select compose file
if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    echo "Using: $COMPOSE_FILE (Production HA Setup)"
else
    COMPOSE_FILE="docker-compose.yml"
    echo "Using: $COMPOSE_FILE (Development Setup)"
fi

# Check environment file
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}⚠️  Creating .env from template...${NC}"
    if [ -f ".env.production" ]; then
        cp .env.production .env
        echo -e "${GREEN}✓ .env created${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env and set secure passwords!${NC}"
    else
        echo -e "${RED}❌ .env.production template not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Build or pull images
echo -e "\n${YELLOW}Setting up Docker images...${NC}"

if [ "$REBUILD" = "true" ]; then
    echo "Rebuilding images..."
    docker-compose -f $COMPOSE_FILE build --no-cache
else
    echo "Pulling images..."
    docker-compose -f $COMPOSE_FILE pull --quiet 2>/dev/null || true
    echo "Building application image..."
    docker-compose -f $COMPOSE_FILE build --quiet
fi

echo -e "${GREEN}✓ Images ready${NC}"

# Stop existing services
if [ "$(docker-compose -f $COMPOSE_FILE ps -q)" ]; then
    echo -e "\n${YELLOW}Stopping existing services...${NC}"
    docker-compose -f $COMPOSE_FILE down
fi

# Start services
echo -e "\n${YELLOW}Starting services...${NC}"
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to be healthy...${NC}"
echo "(This may take 30-60 seconds)"

sleep 10

# Check service health
RETRIES=30
COUNTER=0

echo -e "\n${YELLOW}Health Check:${NC}"

while [ $COUNTER -lt $RETRIES ]; do
    HEALTH_API=$(docker-compose -f $COMPOSE_FILE ps api 2>/dev/null | grep -c "healthy\|running" || echo 0)
    HEALTH_DB=$(docker-compose -f $COMPOSE_FILE ps postgres 2>/dev/null | grep -c "healthy" || echo 0)
    
    if [ $HEALTH_API -gt 0 ] && [ $HEALTH_DB -gt 0 ]; then
        echo -e "${GREEN}✓ All services healthy${NC}"
        break
    fi
    
    COUNTER=$((COUNTER+1))
    echo -n "."
    sleep 2
done

echo ""

# Display service status
echo -e "\n${YELLOW}Service Status:${NC}"
docker-compose -f $COMPOSE_FILE ps

# Display access information
echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
echo -e "\n${YELLOW}Access Information:${NC}"
echo ""
echo "API Server"
echo "  URL:              http://localhost:8000"
echo "  Health Check:     http://localhost:8000/health"
echo "  API Docs:         http://localhost:8000/docs"
echo "  ReDoc:            http://localhost:8000/redoc"
echo ""
echo "Dashboard"
echo "  URL:              http://localhost:8050"
echo ""
echo "Database"
echo "  Host:             localhost"
echo "  Port:             5432"
echo "  PgAdmin:          http://localhost:5050"
echo ""

if [ "$ENVIRONMENT" = "production" ]; then
    echo "Monitoring (Production)"
    echo "  Prometheus:       http://localhost:9090"
    echo "  Grafana:          http://localhost:3000"
    echo ""
fi

echo "Redis"
echo "  URL:              redis://localhost:6379"
echo ""

# Useful commands
echo -e "\n${YELLOW}Useful Commands:${NC}"
echo ""
echo "View logs:"
echo "  docker-compose -f $COMPOSE_FILE logs -f api"
echo "  docker-compose -f $COMPOSE_FILE logs -f dashboard"
echo ""
echo "Stop services:"
echo "  docker-compose -f $COMPOSE_FILE down"
echo ""
echo "Stop and remove volumes (WARNING: deletes data):"
echo "  docker-compose -f $COMPOSE_FILE down -v"
echo ""
echo "View resource usage:"
echo "  docker stats"
echo ""
echo "Execute database command:"
echo "  docker-compose -f $COMPOSE_FILE exec postgres psql -U crypto_trader -d crypto_trading"
echo ""
echo "Backup database:"
echo "  docker-compose -f $COMPOSE_FILE exec postgres pg_dump -U crypto_trader crypto_trading > backup.sql"
echo ""

echo -e "\n${GREEN}Next Steps:${NC}"
echo "1. Access dashboard at http://localhost:8050"
echo "2. Check API docs at http://localhost:8000/docs"
echo "3. Review logs: docker-compose logs -f"
echo "4. For production, configure .env and SSL certificates"
echo ""
echo "📚 For more information, see DEPLOYMENT.md"
echo ""
