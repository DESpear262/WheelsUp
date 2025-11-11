#!/bin/bash

# WheelsUp Docker Environment Verification Script
# Run this script to verify that all services are properly connected

set -e

echo "🔍 Verifying WheelsUp Docker Environment Setup"
echo "==============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    local service=$1
    local status=$2
    local message=$3

    if [ "$status" = "success" ]; then
        echo -e "${GREEN}✅${NC} $service: $message"
    elif [ "$status" = "warning" ]; then
        echo -e "${YELLOW}⚠️${NC}  $service: $message"
    else
        echo -e "${RED}❌${NC} $service: $message"
    fi
}

# Check if docker-compose is running
if ! docker-compose ps | grep -q "Up"; then
    print_status "Docker Compose" "error" "No services are running. Run 'docker-compose up -d' first."
    exit 1
fi

echo "Checking service health..."
echo

# Check PostgreSQL connection
echo "Testing PostgreSQL connection..."
if docker-compose exec -T postgres pg_isready -U wheelsup_user -d wheelsup_dev >/dev/null 2>&1; then
    print_status "PostgreSQL" "success" "Database is accessible"
else
    print_status "PostgreSQL" "error" "Cannot connect to database"
fi

# Check OpenSearch connection
echo "Testing OpenSearch connection..."
if curl -f -s http://localhost:9200/_cluster/health >/dev/null 2>&1; then
    print_status "OpenSearch" "success" "Search service is accessible"
else
    print_status "OpenSearch" "error" "Cannot connect to OpenSearch"
fi

# Check if web service is responding
echo "Testing Web Application..."
if curl -f -s http://localhost:3000 >/dev/null 2>&1; then
    print_status "Web Application" "success" "Next.js app is responding"
else
    print_status "Web Application" "warning" "Web app not responding (may still be building)"
fi

# Check ETL service health
echo "Testing ETL Service..."
if docker-compose exec -T etl python -c "import sys; print('Python OK'); sys.exit(0)" >/dev/null 2>&1; then
    print_status "ETL Service" "success" "Python environment is ready"
else
    print_status "ETL Service" "error" "Python environment has issues"
fi

# Test inter-service communication
echo
echo "Testing inter-service communication..."
echo

# Test web app to database connection (if web app has health endpoint)
if curl -f -s http://localhost:3000/api/health >/dev/null 2>&1; then
    print_status "Web → Database" "success" "Web app can connect to database"
else
    print_status "Web → Database" "warning" "Cannot verify web-to-database connection"
fi

# Test ETL to database connection
if docker-compose exec -T etl python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    conn.close()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" >/dev/null 2>&1; then
    print_status "ETL → Database" "success" "ETL can connect to database"
else
    print_status "ETL → Database" "error" "ETL cannot connect to database"
fi

# Test ETL to OpenSearch connection
if docker-compose exec -T etl python -c "
import os
import requests
try:
    response = requests.get(os.getenv('OPENSEARCH_URL') + '/_cluster/health', timeout=5)
    if response.status_code == 200:
        print('OpenSearch connection successful')
    else:
        print('OpenSearch returned non-200 status')
        exit(1)
except Exception as e:
    print(f'OpenSearch connection failed: {e}')
    exit(1)
" >/dev/null 2>&1; then
    print_status "ETL → OpenSearch" "success" "ETL can connect to OpenSearch"
else
    print_status "ETL → OpenSearch" "error" "ETL cannot connect to OpenSearch"
fi

echo
echo "📊 Service Status Summary:"
echo "=========================="
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo
echo "🔧 Useful Commands:"
echo "==================="
echo "View logs:           docker-compose logs [service-name]"
echo "Access database:     docker-compose exec postgres psql -U wheelsup_user -d wheelsup_dev"
echo "Access OpenSearch:   curl http://localhost:9200/_cluster/health"
echo "Restart services:    docker-compose restart"
echo "Stop environment:    docker-compose down"

echo
print_status "Verification" "success" "Docker environment verification complete!"
