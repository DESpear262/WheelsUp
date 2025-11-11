# WheelsUp Docker Development Environment

This directory contains the Docker configuration for the WheelsUp development environment.

## Services

- **postgres**: PostgreSQL 16 with PostGIS 3.4 (simulates RDS)
- **opensearch**: OpenSearch 2.13 (simulates AWS OpenSearch Service)
- **web**: Next.js application (Node.js 22)
- **etl**: ETL pipeline (Python 3.14)

## Quick Start

1. **Set up environment variables**:
   ```bash
   cp apps/web/.env.example apps/web/.env
   cp etl/.env.example etl/.env
   # Edit .env files with your actual values
   ```

2. **Start the development environment**:
   ```bash
   docker-compose up -d
   ```

3. **Check service health**:
   ```bash
   docker-compose ps
   docker-compose logs [service-name]
   ```

4. **Access services**:
   - Web App: http://localhost:3000
   - PostgreSQL: localhost:5432 (user: wheelsup_user, db: wheelsup_dev)
   - OpenSearch: http://localhost:9200

## Development Workflow

### Hot Reloading
- Web app supports hot reloading with volume mounts
- ETL service keeps container running for development commands

### Database Management
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U wheelsup_user -d wheelsup_dev

# View OpenSearch cluster health
curl http://localhost:9200/_cluster/health
```

### ETL Development
```bash
# Run ETL commands
docker-compose exec etl python run_etl.py --help

# Install additional packages (temporary)
docker-compose exec etl pip install package-name
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in `docker-compose.override.yml`
2. **Memory issues**: Adjust JVM settings for OpenSearch
3. **Permission issues**: Ensure proper file permissions on mounted volumes

### Logs and Debugging
```bash
# View all logs
docker-compose logs

# Follow logs for specific service
docker-compose logs -f web

# View container resource usage
docker stats
```

### Reset Environment
```bash
# Stop and remove containers/volumes
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```
