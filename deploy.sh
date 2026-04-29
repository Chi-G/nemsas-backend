#!/bin/bash

# ============================================================================
# NEMSAS FastAPI Deployment Script
# ============================================================================
# This script handles automated deployment to the VPS
# Called by GitHub Actions workflow_dispatch

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# CONFIGURATION
# ============================================================================
DEPLOY_USER="${DEPLOY_USER:-$(whoami)}"
DEPLOY_PATH="${PWD}"
DEPLOY_PORT="${DEPLOY_PORT:-9000}"
PROJECT_NAME="nemsas-backend"
APP_SERVICE_NAME="app"
CONTAINER_NAME="nemsas-backend"
DOCKER_COMPOSE_FILE="${DEPLOY_PATH}/docker-compose.yml"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 NEMSAS FASTAPI DEPLOYMENT${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Deploy Path: ${DEPLOY_PATH}"
echo "App Port: ${DEPLOY_PORT}"
echo "User: ${DEPLOY_USER}"
echo "Timestamp: $(date)"
echo -e "${BLUE}========================================${NC}"

# ============================================================================
# VALIDATION
# ============================================================================
echo -e "\n${YELLOW}[1/7] Validating environment...${NC}"

if [ ! -f "${DOCKER_COMPOSE_FILE}" ]; then
    echo -e "${RED}❌ ERROR: docker-compose.yml not found at ${DOCKER_COMPOSE_FILE}${NC}"
    exit 1
fi
echo -e "${GREEN}✅ docker-compose.yml found${NC}"

if [ ! -f "${DEPLOY_PATH}/.env" ]; then
    echo -e "${RED}❌ ERROR: .env file not found at ${DEPLOY_PATH}/.env${NC}"
    echo -e "${YELLOW}Please ensure .env file is present with database and environment variables${NC}"
    exit 1
fi
echo -e "${GREEN}✅ .env file found${NC}"

# Verify Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ ERROR: Docker not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker installed: $(docker --version)${NC}"

if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ ERROR: Docker Compose not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose available${NC}"

# ============================================================================
# PRE-DEPLOYMENT
# ============================================================================
echo -e "\n${YELLOW}[2/7] Backing up current state...${NC}"

BACKUP_DIR="${DEPLOY_PATH}/.backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "${BACKUP_DIR}"

# Save docker-compose state
if [ -f "${DOCKER_COMPOSE_FILE}" ]; then
    cp "${DOCKER_COMPOSE_FILE}" "${BACKUP_DIR}/"
    echo -e "${GREEN}✅ Backup created: ${BACKUP_DIR}${NC}"
fi

# ============================================================================
# STOP EXISTING CONTAINERS
# ============================================================================
echo -e "\n${YELLOW}[3/7] Stopping existing containers...${NC}"

cd "${DEPLOY_PATH}"

if docker compose ps | grep -q "${CONTAINER_NAME}"; then
    docker compose down
    sleep 2
    echo -e "${GREEN}✅ Containers stopped${NC}"
else
    echo -e "${YELLOW}⚠️  No running containers found${NC}"
fi

# ============================================================================
# BUILD IMAGES
# ============================================================================
echo -e "\n${YELLOW}[4/7] Building Docker images...${NC}"

# Use direct docker build for maximum stability
docker build -t nemsas-backend-app . --no-cache

echo -e "${GREEN}✅ Images built successfully${NC}"

# ============================================================================
# START CONTAINERS
# ============================================================================
echo -e "\n${YELLOW}[5/8] Starting containers...${NC}"

# Source .env to get DB variables
set -a
source .env 2>/dev/null || true
set +a

# Use values from .env or defaults
DB_USER=${DB_USER:-nemsas}
DB_PASSWORD=${DB_PASSWORD:-nemsas_password}
DB_NAME=${DB_NAME:-nemsas_db}

DEPLOY_PORT=${DEPLOY_PORT} DB_USER=${DB_USER} DB_PASSWORD=${DB_PASSWORD} DB_NAME=${DB_NAME} \
docker compose up -d

sleep 3  # Give services time to start

echo -e "${GREEN}✅ Containers started${NC}"

# ============================================================================
# HEALTH CHECK
# ============================================================================
echo -e "\n${YELLOW}[6/7] Checking container health...${NC}"

MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker compose ps --services --status running | grep -qx "${APP_SERVICE_NAME}"; then
        echo -e "${GREEN}✅ Container is running${NC}"

        # Wait for API to be ready on the published host port.
        if curl -f -s http://localhost:${DEPLOY_PORT}/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ API is responding${NC}"
            break
        fi
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
        echo "Waiting for service to be ready... (Attempt $ATTEMPT/$MAX_ATTEMPTS)"
        sleep 2
    fi
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${RED}❌ Container failed to start properly${NC}"
    echo -e "${YELLOW}Logs:${NC}"
    docker compose logs -n 20
    exit 1
fi

# ============================================================================
# CLEANUP
# ============================================================================
echo -e "\n${YELLOW}[7/7] Cleaning up...${NC}"

# Prune unused images (keep last 5)
docker image prune -a -f --filter "until=240h" > /dev/null 2>&1

echo -e "${GREEN}✅ Cleanup completed${NC}"

# ============================================================================
# POST-DEPLOYMENT SUMMARY
# ============================================================================
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Service:      ${PROJECT_NAME}"
echo "Port:         ${DEPLOY_PORT}"
echo "Status:       $(docker compose ps --services --status running | grep -x "${APP_SERVICE_NAME}" || echo "not-running")"
echo "Deployed at:  $(date)"
echo ""
echo "🔗 Access URL: http://localhost:${DEPLOY_PORT}"
echo "📚 API Docs:   http://localhost:${DEPLOY_PORT}/docs"
echo ""
echo -e "${BLUE}========================================${NC}"
echo "Useful commands:"
echo "  View logs:      docker compose logs -f app"
echo "  Check status:   docker compose ps"
echo "  Restart:        docker compose restart"
echo -e "${BLUE}========================================${NC}"

exit 0
