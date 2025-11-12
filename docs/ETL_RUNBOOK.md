# WheelsUp ETL Runbook

## Overview

This runbook provides comprehensive instructions for running the WheelsUp ETL (Extract, Transform, Load) pipeline locally and in production environments. The ETL pipeline crawls flight school data, extracts structured information using LLMs, and loads it into PostgreSQL and OpenSearch.

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Pipeline Execution](#pipeline-execution)
- [Testing](#testing)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Production Deployment](#production-deployment)
- [Data Validation](#data-validation)

## Architecture

### Pipeline Stages

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Source URLs   │───▶│   Crawl Stage   │───▶│   Extract Stage │
│                 │    │                 │    │                 │
│ • FAA Websites  │    │ • Scrapy        │    │ • trafilatura   │
│ • Directories   │    │ • Playwright    │    │ • pdfminer      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Raw Storage   │    │   LLM Stage     │    │   Validate      │
│                 │    │                 │    │   Stage         │
│ • S3 Raw Files  │    │ • Claude 3.5    │    │ • Pydantic      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Normalize     │    │   Publish       │    │   Index         │
│   Stage         │    │   Stage         │    │   Stage         │
│                 │    │                 │    │                 │
│ • Data Cleanup  │    │ • PostgreSQL    │    │ • OpenSearch    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

- **Crawl Stage**: Scrapy spiders + Playwright for JavaScript-heavy sites
- **Extract Stage**: Text extraction from HTML/PDF using trafilatura/pdfminer
- **LLM Stage**: Claude 3.5 Sonnet for structured data extraction
- **Validate Stage**: Pydantic schema validation
- **Normalize Stage**: Data cleaning and standardization
- **Publish Stage**: Load to PostgreSQL with Drizzle ORM
- **Index Stage**: Load to OpenSearch for search functionality

## Prerequisites

### System Requirements

- **Python 3.14**
- **Node.js 22 LTS** (for database operations)
- **Docker & Docker Compose**
- **PostgreSQL client tools** (optional, for debugging)

### Environment Variables

Create `etl/.env` file:

```bash
# Database connections
DATABASE_URL="postgresql://wheelsup_user:wheelsup_password@localhost:5432/wheelsup_dev"
OPENSEARCH_URL="http://localhost:9200"

# LLM APIs (required for extraction)
ANTHROPIC_API_KEY="your-anthropic-key"
OPENAI_API_KEY="your-openai-fallback-key"

# AWS (for production S3 storage)
AWS_ACCESS_KEY_ID="your-aws-key"
AWS_SECRET_ACCESS_KEY="your-aws-secret"
AWS_REGION="us-east-1"
AWS_S3_BUCKET="wheelsup-raw-data"

# Logging and debugging
LOG_LEVEL="INFO"
DEBUG_MODE="false"
```

### API Keys Setup

1. **Anthropic Claude API**:
   - Sign up at [anthropic.com](https://anthropic.com)
   - Generate API key from dashboard
   - Add to `.env` as `ANTHROPIC_API_KEY`

2. **OpenAI API** (fallback):
   - Sign up at [openai.com](https://openai.com)
   - Generate API key
   - Add to `.env` as `OPENAI_API_KEY`

## Local Development Setup

### 1. Start Infrastructure

```bash
# From project root
docker-compose up -d postgres opensearch

# Verify services are running
docker-compose ps
curl http://localhost:9200/_cluster/health
```

### 2. Install Dependencies

```bash
cd etl

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Verify installations
python -c "import scrapy, trafilatura, anthropic; print('✅ All dependencies installed')"
```

### 3. Initialize Database Schema

```bash
# From apps/web directory
cd ../apps/web
npm install
npm run db:push  # Apply schema migrations
```

### 4. Verify Configuration

```bash
# Test database connection
cd ../etl
python -c "
import os
from utils.db_connection import get_db_connection
conn = get_db_connection()
print('✅ Database connection successful')
conn.close()
"

# Test OpenSearch connection
python -c "
import requests
response = requests.get('http://localhost:9200/_cluster/health')
print(f'✅ OpenSearch status: {response.json()[\"status\"]}')
"
```

## Pipeline Execution

### Full Pipeline Run

```bash
# From etl/ directory
cd etl

# Run complete pipeline with timestamp-based snapshot ID
python run_etl.py --snapshot $(date +%Y%m%d_%H%M%S)

# Or use a descriptive snapshot ID
python run_etl.py --snapshot "test_run_$(date +%Y%m%d)"
```

### Selective Pipeline Execution

```bash
# Run only specific stages
python run_etl.py --stages crawl,extract --snapshot test_partial

# Available stages: discover, crawl, extract, llm, validate, normalize, publish, index
```

### Configuration Options

```bash
python run_etl.py [options]

Options:
  --snapshot SNAPSHOT_ID    Required: Unique identifier for this ETL run
  --stages STAGES           Comma-separated list of stages to run
  --sources SOURCES         Comma-separated list of sources to crawl
  --max-pages MAX_PAGES     Maximum pages to crawl per source (default: 100)
  --concurrency CONCURRENCY Number of concurrent requests (default: 5)
  --dry-run                 Show what would be done without executing
  --verbose                 Enable verbose logging
  --help                    Show help message
```

### Example Runs

```bash
# Quick test run with limited data
python run_etl.py --snapshot quick_test --max-pages 5 --concurrency 2

# Production-style run
python run_etl.py --snapshot 20251115_full_crawl --concurrency 10

# Debug specific source
python run_etl.py --snapshot debug_faa --sources faa_flightschools --verbose
```

## Testing

### Pipeline Component Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest test_pipeline.py        # Pipeline integration tests
pytest test_crawl_integration.py  # Crawling tests
pytest test_data_publish.py    # Data publishing tests

# Run with coverage
pytest --cov=. --cov-report=html
```

### Individual Component Testing

```bash
# Test spider functionality
python test_pipeline.py --spider faa_flightschools

# Test extraction pipeline
python test_extraction.py --input test_data/sample.html

# Test LLM extraction
python -c "
from pipelines.llm.extract_school_data import extract_school_info
result = extract_school_info('Sample flight school website text...')
print(result)
"
```

### Data Validation

```bash
# Validate extracted data against schemas
python test_validation.py --input extracted_text/ --schema schemas/

# Check data quality metrics
python -c "
from utils.data_quality import calculate_quality_metrics
metrics = calculate_quality_metrics('extracted_text/')
print(f'Completeness: {metrics[\"completeness\"]}%')
print(f'Accuracy: {metrics[\"accuracy\"]}%')
"
```

## Monitoring & Troubleshooting

### Log Files

Pipeline logs are stored in:
- `etl/logs/` - Main pipeline execution logs
- `etl/test_output/logs/` - Test execution logs
- Docker container logs: `docker-compose logs etl`

### Common Issues

#### Database Connection Issues

```bash
# Check database status
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Test connection manually
psql "postgresql://wheelsup_user:wheelsup_password@localhost:5432/wheelsup_dev" -c "SELECT 1;"
```

**Solutions:**
- Ensure PostgreSQL container is running
- Check DATABASE_URL in .env file
- Verify database schema is initialized

#### OpenSearch Connection Issues

```bash
# Check OpenSearch health
curl http://localhost:9200/_cluster/health

# View OpenSearch logs
docker-compose logs opensearch

# Reset OpenSearch (development only)
docker-compose down opensearch
docker volume rm wheelsup_opensearch_data
docker-compose up opensearch
```

#### Crawling Issues

```bash
# Test spider connectivity
python -c "
from pipelines.crawl.spiders.faa_flightschools import FAASpider
spider = FAASpider()
print('Spider initialized successfully')
"
```

**Common fixes:**
- Check network connectivity
- Verify robots.txt compliance
- Adjust crawl delays in settings
- Update User-Agent headers

#### LLM API Issues

```bash
# Test API connectivity
python -c "
import anthropic
client = anthropic.Anthropic()
print('Claude API connection successful')
"
```

**Solutions:**
- Verify API keys in .env
- Check API rate limits
- Monitor API costs
- Implement retry logic with exponential backoff

### Performance Optimization

#### Memory Usage
```bash
# Monitor Python memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

#### Database Performance
```bash
# Check slow queries
psql "postgresql://wheelsup_user:wheelsup_password@localhost:5432/wheelsup_dev" -c "
SELECT query, total_time, calls
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
"
```

#### Crawling Performance
- Adjust `CONCURRENT_REQUESTS` in `configs/crawl_settings.yaml`
- Implement crawl delays to respect site policies
- Use browser pools for JavaScript-heavy sites

## Production Deployment

### Infrastructure Setup

```bash
# Deploy infrastructure with Terraform
cd infra/terraform
terraform init
terraform plan
terraform apply

# Verify infrastructure
aws ec2 describe-instances --filters "Name=tag:Name,Values=wheelsup-etl"
aws rds describe-db-instances --db-instance-identifier wheelsup-db
```

### Production ETL Execution

```bash
# On EC2 instance
cd /opt/wheelsup/etl

# Full production run
python run_etl.py \
  --snapshot $(date +%Y%m%d_%H%M%S) \
  --concurrency 20 \
  --max-pages 1000

# Monitor execution
tail -f logs/etl_$(date +%Y%m%d).log
```

### Automated Scheduling

```bash
# Add to crontab for weekly runs
crontab -e

# Weekly ETL run every Sunday at 2 AM
0 2 * * 0 cd /opt/wheelsup/etl && python run_etl.py --snapshot weekly_$(date +\%Y\%m\%d)
```

### Backup and Recovery

```bash
# Database backup
pg_dump "postgresql://user:pass@host:5432/db" > backup_$(date +%Y%m%d).sql

# OpenSearch snapshot
curl -X PUT "localhost:9200/_snapshot/my_backup/snapshot_$(date +%Y%m%d)" \
  -H 'Content-Type: application/json' \
  -d '{"indices": "wheelsup-*"}'
```

## Data Validation

### Quality Metrics

```bash
# Generate quality report
python -c "
from utils.data_quality import generate_quality_report
report = generate_quality_report('output/', '20251115_full_crawl')
print(f'Schools extracted: {report[\"total_schools\"]}')
print(f'Completeness: {report[\"completeness_percentage\"]}%')
print(f'Confidence: {report[\"average_confidence\"]}')
"
```

### Data Consistency Checks

```bash
# Validate against schemas
python test_validation.py --snapshot 20251115_full_crawl

# Cross-reference checks
python -c "
from utils.data_integrity import check_data_integrity
issues = check_data_integrity('20251115_full_crawl')
if issues:
    print('Data integrity issues found:')
    for issue in issues:
        print(f'  - {issue}')
else:
    print('✅ All data integrity checks passed')
"
```

### Performance Benchmarks

```bash
# Benchmark extraction performance
python -c "
import time
from pipelines.llm.extract_school_data import benchmark_extraction

start_time = time.time()
results = benchmark_extraction('test_data/')
end_time = time.time()

print(f'Extraction rate: {len(results) / (end_time - start_time):.1f} schools/second')
"
```

## Emergency Procedures

### Pipeline Failure Recovery

```bash
# Resume from specific stage
python run_etl.py --snapshot recovery_run --stages validate,normalize,publish,index

# Reprocess failed items
python run_etl.py --snapshot fix_run --failed-only --snapshot-to-fix 20251115_failed
```

### Data Rollback

```bash
# Rollback database changes
cd apps/web
npm run db:rollback -- --snapshot 20251115_problematic

# Rollback OpenSearch index
curl -X POST "localhost:9200/_snapshot/my_backup/snapshot_20251114/_restore" \
  -H 'Content-Type: application/json' \
  -d '{"indices": "wheelsup-*"}'
```

### Alert Configuration

```bash
# Set up monitoring alerts
# 1. ETL pipeline completion
# 2. Data quality thresholds
# 3. API rate limit warnings
# 4. Database connection issues
```

## Maintenance Tasks

### Weekly Tasks
- Review ETL logs for errors
- Update spider configurations for site changes
- Monitor LLM API usage and costs
- Verify data quality metrics

### Monthly Tasks
- Update Python dependencies
- Review and optimize database indexes
- Analyze crawl success rates
- Update documentation

### Quarterly Tasks
- Full data quality audit
- Performance benchmarking
- Cost optimization review
- Infrastructure scaling assessment

---

**ETL Runbook** - Updated for WheelsUp MVP production deployment.
