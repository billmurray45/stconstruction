#!/bin/bash
#
# Health Check Script for Construction Website
# Checks if application and database are healthy
#
# Usage:
#   ./health-check.sh [prod|dev|both]
#
# Examples:
#   ./health-check.sh prod     # Check production only
#   ./health-check.sh dev      # Check staging only
#   ./health-check.sh both     # Check both (default)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROD_URL="https://site.com"
DEV_URL="https://dev.site.com"
TIMEOUT=5

# Function to check health endpoint
check_health() {
    local name=$1
    local url=$2
    local endpoint=$3

    echo -n "Checking $name $endpoint... "

    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url$endpoint" 2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    elif [ "$response" = "503" ]; then
        echo -e "${YELLOW}⚠ Degraded${NC} (HTTP $response)"
        return 1
    elif [ "$response" = "000" ]; then
        echo -e "${RED}✗ Timeout${NC} (no response)"
        return 2
    else
        echo -e "${RED}✗ Failed${NC} (HTTP $response)"
        return 1
    fi
}

# Function to check all endpoints for an environment
check_environment() {
    local name=$1
    local url=$2

    echo ""
    echo "===== $name Environment ====="

    check_health "$name" "$url" "/health"
    app_status=$?

    check_health "$name" "$url" "/health/db"
    db_status=$?

    if [ $app_status -eq 0 ] && [ $db_status -eq 0 ]; then
        echo -e "${GREEN}Overall: Healthy${NC}"
        return 0
    else
        echo -e "${RED}Overall: Unhealthy${NC}"
        return 1
    fi
}

# Main
MODE=${1:-both}

case $MODE in
    prod)
        check_environment "Production" "$PROD_URL"
        exit $?
        ;;
    dev)
        check_environment "Staging" "$DEV_URL"
        exit $?
        ;;
    both)
        check_environment "Production" "$PROD_URL"
        prod_result=$?

        check_environment "Staging" "$DEV_URL"
        dev_result=$?

        echo ""
        if [ $prod_result -eq 0 ] && [ $dev_result -eq 0 ]; then
            echo -e "${GREEN}All services are healthy!${NC}"
            exit 0
        else
            echo -e "${RED}Some services are unhealthy!${NC}"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 [prod|dev|both]"
        exit 1
        ;;
esac
