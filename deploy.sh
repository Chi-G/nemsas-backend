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
echo -e "\n${YELLOW}[1/6] Validating environment...${NC}"

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

DOCKER_COMPOSE_CMD="docker compose"
if ! $DOCKER_COMPOSE_CMD version &> /dev/null; then
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        echo -e "${RED}❌ ERROR: Docker Compose not installed${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ Docker Compose available: $($DOCKER_COMPOSE_CMD version)${NC}"

# ============================================================================
# PRE-DEPLOYMENT
# ============================================================================
echo -e "\n${YELLOW}[2/6] Backing up current state...${NC}"

BACKUP_DIR="${DEPLOY_PATH}/.backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "${BACKUP_DIR}"

# Save docker-compose state
if [ -f "${DOCKER_COMPOSE_FILE}" ]; then
    cp "${DOCKER_COMPOSE_FILE}" "${BACKUP_DIR}/"
    echo -e "${GREEN}✅ Backup created: ${BACKUP_DIR}${NC}"
fi

# ============================================================================
# BUILD IMAGES (ZERO-DOWNTIME PREPARATION)
# ============================================================================
echo -e "\n${YELLOW}[3/6] Building new container images...${NC}"
echo "Checking disk space before building..."
df -h /

# Build the images (keeps the old app running while building, uses cache for speed)
echo "Building ${APP_SERVICE_NAME} image (utilizing layer cache)..."
if ! $DOCKER_COMPOSE_CMD build --progress=plain ${APP_SERVICE_NAME}; then
    echo -e "${RED}❌ Image build failed! Checking Docker system info...${NC}"
    docker info | grep -E "Storage|Space|Disk"
    exit 1
fi
echo -e "${GREEN}✅ ${APP_SERVICE_NAME} image built successfully${NC}"

# ============================================================================
# START/UP CONTAINERS (INSTANT SWITCHOVER)
# ============================================================================
echo -e "\n${YELLOW}[4/6] Performing zero-downtime container switchover...${NC}"

# TEMPORARY FIX: Restart DB to clear lingering locks
echo "Temporarily restarting DB container to clear locks..."
$DOCKER_COMPOSE_CMD restart db

echo "Recreating and starting ${APP_SERVICE_NAME} container..."
if ! $DOCKER_COMPOSE_CMD up -d --force-recreate ${APP_SERVICE_NAME}; then
    echo -e "${RED}❌ Container switchover failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ ${APP_SERVICE_NAME} container restarted and running successfully${NC}"

# ============================================================================
# HEALTH CHECK
# ============================================================================
echo -e "\n${YELLOW}[5/6] Checking container health...${NC}"

MAX_ATTEMPTS=60
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if $DOCKER_COMPOSE_CMD ps --services --status running | grep -qx "${APP_SERVICE_NAME}"; then
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
    echo -e "${YELLOW}Final Logs:${NC}"
    $DOCKER_COMPOSE_CMD logs --tail 100
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}📡 STARTUP LOGS (Check Seeding Status):${NC}"
$DOCKER_COMPOSE_CMD logs --tail 300 ${APP_SERVICE_NAME}
echo -e "${BLUE}========================================${NC}"

# ============================================================================
# CLEANUP
# ============================================================================
echo -e "\n${YELLOW}[6/6] Cleaning up...${NC}"

# Prune unused images (keep last 5)
docker image prune -a -f --filter "until=240h" > /dev/null 2>&1

echo -e "${GREEN}✅ Cleanup completed${NC}"

# ============================================================================
# POST-DEPLOYMENT SUMMARY
# ============================================================================
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}🚀 DEPLOYMENT SUCCESSFUL (6/6)${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Service:      ${PROJECT_NAME}"
echo "Port:         ${DEPLOY_PORT}"
echo "Status:       $($DOCKER_COMPOSE_CMD ps --services --status running | grep -x "${APP_SERVICE_NAME}" || echo "not-running")"
echo "Deployed at:  $(date)"
echo ""
echo "🔗 Access URL: http://localhost:${DEPLOY_PORT}"
echo "📚 API Docs:   http://localhost:${DEPLOY_PORT}/docs"
echo ""
echo -e "${BLUE}========================================${NC}"
echo "Useful commands:"
echo "  View logs:      $DOCKER_COMPOSE_CMD logs -f app"
echo "  Check status:   $DOCKER_COMPOSE_CMD ps"
echo "  Restart:        $DOCKER_COMPOSE_CMD restart"
echo -e "${BLUE}========================================${NC}"

exit 0
