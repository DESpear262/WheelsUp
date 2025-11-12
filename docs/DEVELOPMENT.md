# WheelsUp Development Guide

## Overview

WheelsUp is a flight school marketplace MVP that aggregates, normalizes, and presents flight school data to help students compare training options. This guide provides comprehensive information for developers working on the project.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Local Development Setup](#local-development-setup)
- [Development Workflow](#development-workflow)
- [Code Quality Standards](#code-quality-standards)
- [Testing Strategy](#testing-strategy)
- [Database Schema](#database-schema)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│   ETL Pipeline  │───▶│   Web Frontend  │
│                 │    │                 │    │                 │
│ • FAA Websites  │    │ • Scrapy        │    │ • Next.js       │
│ • Directories   │    │ • Playwright    │    │ • TypeScript    │
│ • Google Places │    │ • Claude 3.5    │    │ • Tailwind      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Raw Storage   │    │   PostgreSQL    │    │   OpenSearch    │
│                 │    │   (RDS)         │    │   Service       │
│ • S3 Raw Files  │    │ • PostGIS       │    │ • Faceted       │
│ • JSON Extracts │    │ • Drizzle ORM   │    │ • Search        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **Data Acquisition**: Scrapy spiders crawl flight school websites and directories
2. **Text Extraction**: Playwright handles JavaScript-heavy sites, trafilatura extracts clean text
3. **LLM Processing**: Claude 3.5 Sonnet extracts structured data from unstructured content
4. **Data Validation**: Pydantic validates extracted data against schemas
5. **Storage**: Data loads into PostgreSQL (relational) and OpenSearch (search)
6. **API Serving**: Next.js API routes serve data to React frontend
7. **User Interface**: Searchable interface with filters, maps, and comparisons

### Key Design Patterns

- **Snapshot-based ETL**: Each pipeline run creates immutable data snapshots
- **Provenance Tracking**: Every data field includes source, timestamp, and confidence
- **Multi-source Aggregation**: Combines data from websites, directories, and metadata
- **LLM-powered Extraction**: Uses Claude 3.5 for structured data extraction
- **Type-safe APIs**: Full TypeScript coverage from database to frontend

## Technology Stack

### Frontend (apps/web/)
- **Framework**: Next.js 15.0.3 with App Router
- **Language**: TypeScript 5.6
- **Styling**: Tailwind CSS 3.4 + shadcn/ui components
- **Mapping**: Mapbox GL JS 3.3
- **ORM**: Drizzle ORM 0.33
- **Testing**: Jest + React Testing Library
- **Linting**: ESLint with Next.js config

### Backend & ETL (etl/)
- **Runtime**: Python 3.14
- **Crawling**: Scrapy 2.12 + Playwright 1.48
- **LLM**: Claude 3.5 Sonnet (primary), GPT-4o (fallback)
- **Validation**: Pydantic 3.0
- **Text Processing**: trafilatura 1.9.0, pdfminer.six
- **Database**: PostgreSQL 16 + PostGIS 3.4
- **Search**: Amazon OpenSearch Service 2.13

### Infrastructure
- **Containers**: Docker + Docker Compose
- **Cloud**: AWS (EC2, RDS, OpenSearch, S3, VPC)
- **IaC**: Terraform 1.10+
- **CI/CD**: GitHub Actions

## Local Development Setup

### Prerequisites

- **Docker & Docker Compose** (v2.0+)
- **Node.js 22 LTS**
- **Python 3.14**
- **Git**
- **VS Code** (recommended) with Cursor extension

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd wheelsup
   ```

2. **Start the development environment**:
   ```bash
   # Start all services (Postgres, OpenSearch, etc.)
   docker-compose up -d

   # Verify services are running
   docker-compose ps
   ```

3. **Install dependencies**:
   ```bash
   # Frontend dependencies
   cd apps/web
   npm install

   # ETL dependencies
   cd ../etl
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   # Copy example files
   cp apps/web/.env.example apps/web/.env
   cp etl/.env.example etl/.env

   # Edit .env files with your local configuration
   # See DEPLOYMENT.md for configuration details
   ```

5. **Initialize the database**:
   ```bash
   # Run database migrations (from apps/web/)
   cd apps/web
   npm run db:push

   # Seed with sample data (optional)
   npm run db:seed
   ```

6. **Start development servers**:
   ```bash
   # Terminal 1: Frontend (from apps/web/)
   npm run dev

   # Terminal 2: ETL development (from etl/)
   # Services run on-demand, see ETL_RUNBOOK.md
   ```

7. **Access the application**:
   - **Frontend**: http://localhost:3000
   - **Database**: localhost:5432 (user: wheelsup_user, db: wheelsup_dev)
   - **OpenSearch**: http://localhost:9200

### Environment Configuration

#### Frontend (.env)
```bash
# Database
DATABASE_URL="postgresql://wheelsup_user:wheelsup_password@localhost:5432/wheelsup_dev"

# Search
OPENSEARCH_URL="http://localhost:9200"

# External APIs
NEXT_PUBLIC_MAPBOX_TOKEN="your-mapbox-token"
MAPBOX_ACCESS_TOKEN="your-mapbox-token"

# Development
NODE_ENV="development"
NEXT_PUBLIC_API_URL="http://localhost:3000"
```

#### ETL (.env)
```bash
# Database
DATABASE_URL="postgresql://wheelsup_user:wheelsup_password@localhost:5432/wheelsup_dev"

# Search
OPENSEARCH_URL="http://localhost:9200"

# LLM APIs
ANTHROPIC_API_KEY="your-anthropic-key"
OPENAI_API_KEY="your-openai-key"

# AWS (for production deployments)
AWS_ACCESS_KEY_ID="your-aws-key"
AWS_SECRET_ACCESS_KEY="your-aws-secret"
AWS_REGION="us-east-1"
```

## Development Workflow

### Code Organization

```
apps/web/
├── app/                 # Next.js App Router
│   ├── api/            # API routes
│   ├── layout.tsx      # Root layout
│   └── page.tsx        # Home page
├── components/         # Reusable UI components
├── lib/                # Business logic & utilities
│   ├── db.ts          # Database connection
│   ├── Newsearch.ts   # Search client
│   └── types.ts       # TypeScript types
├── drizzle/            # Database schema & migrations
├── public/             # Static assets
└── __tests__/          # Unit tests

etl/
├── pipelines/          # ETL pipeline code
│   ├── crawl/         # Data acquisition
│   ├── extract/       # Text extraction
│   └── llm/           # LLM processing
├── schemas/           # Pydantic models
├── utils/             # Shared utilities
└── test_*.py          # Test files
```

### Commit Guidelines

We use conventional commits with agent coordination:

```bash
# Good examples
[AgentName] PR-2.1: New → Planning [Database Schema]
[White] PR-3.2: Planning → Complete [Frontend Components]

# Commit message format
[AgentName] PR-X.Y: Status Change [Brief Description]
```

### Multi-Agent Coordination

This project uses coordinated AI agents. Key rules:

1. **Identity Management**: Each agent claims a unique identity (White, Orange, Blonde, Pink, Blue, Brown)
2. **File Locking**: Files are locked while PRs are In Progress or Suspended
3. **Task Assignment**: Work on one PR at a time, update status appropriately
4. **Memory Bank**: Update `docs/memory/` files for significant changes

### Code Quality Standards

#### Function Size Limits
- **Maximum 75 lines per function**
- Break complex functions into smaller, focused helpers
- Each function should have a single, clear responsibility

#### File Size Limits
- **Maximum 750 lines per file**
- Split large files by logical boundaries
- Prefer many small files over few large ones

#### TypeScript Requirements
- **100% type coverage** - no `any` types in production code
- Use strict TypeScript configuration
- Define interfaces for all data structures

#### Testing Requirements
- **80%+ code coverage** target
- Unit tests for all business logic
- Integration tests for API endpoints
- Mock external dependencies

### Database Development

#### Schema Changes
```bash
# Generate migration from schema changes
cd apps/web
npm run db:generate

# Apply migrations to local database
npm run db:push

# Reset database (development only)
npm run db:reset
```

#### Query Patterns
```typescript
// Use Drizzle ORM for type-safe queries
import { db } from '@/lib/db';
import { schools } from '@/drizzle/schema';

// Find schools with filters
const result = await db
  .select()
  .from(schools)
  .where(sql`${schools.state} = ${state}`)
  .limit(20);

// Insert with validation
await db.insert(schools).values(newSchoolData);
```

### API Development

#### Route Structure
```typescript
// app/api/schools/route.ts
export async function GET(request: NextRequest) {
  // Parameter validation
  // Business logic
  // Response formatting
  return NextResponse.json(data);
}
```

#### Error Handling
```typescript
// Centralized error handling
try {
  // API logic
} catch (error) {
  return handleApiError(error); // User-friendly error responses
}
```

### Testing Strategy

#### Unit Tests
```typescript
// lib/__tests__/db.test.ts
describe('Database Layer', () => {
  test('should handle connection errors', async () => {
    // Test error scenarios
  });
});
```

#### API Tests
```typescript
// __tests__/api.test.ts
describe('Schools API', () => {
  test('GET /api/schools returns paginated results', async () => {
    // Test API endpoints
  });
});
```

#### Running Tests
```bash
# Frontend tests
cd apps/web
npm test                    # Run all tests
npm run test:coverage      # With coverage report
npm run test:watch         # Watch mode

# ETL tests
cd etl
pytest                     # Run Python tests
pytest --cov=.            # With coverage
```

## Database Schema

### Core Tables

#### Schools
Flight school information with location, accreditation, and contact details.

#### Programs
Training programs offered by schools (PPL, IR, CPL, etc.).

#### Pricing
Cost information for programs and services.

#### Metrics
Performance data and reliability metrics.

#### Attributes
Additional school-specific information.

### Key Relationships

```
Schools (1) ──── (N) Programs
   │
   ├── (N) Pricing
   ├── (N) Metrics
   └── (N) Attributes
```

### Indexing Strategy

- **Geospatial**: PostGIS for location queries
- **Full-text**: OpenSearch for complex search
- **Composite**: Optimized for common filter combinations
- **Partial**: Active records only

## API Documentation

### Schools API

#### GET /api/schools
Search and filter flight schools.

**Query Parameters:**
- `city`, `state` - Location filters
- `vaApproved` - VA approval status
- `minRating` - Minimum rating filter
- `page`, `limit` - Pagination
- `sortBy`, `sortOrder` - Sorting

**Response:**
```json
{
  "schools": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalCount": 150,
    "hasNext": true
  },
  "metadata": {
    "snapshotId": "2025Q1-MVP",
    "asOf": "2025-01-15T10:00:00Z"
  }
}
```

#### GET /api/schools/[id]
Get detailed information for a specific school.

**Query Parameters:**
- `includePrograms` - Include program data
- `includePricing` - Include pricing data
- `includeMetrics` - Include metrics data

### Metadata API

#### GET /api/meta
Get system metadata and statistics.

**Response:**
```json
{
  "snapshotId": "20251111_crawl",
  "lastEtlRun": "2025-11-11T14:30:00Z",
  "coverage": {
    "totalSchools": 150,
    "schoolsWithPricing": 120,
    "geographicCoverage": {
      "statesCovered": 45,
      "countriesCovered": 1
    }
  }
}
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Reset database
cd apps/web
npm run db:reset
```

#### OpenSearch Issues
```bash
# Check OpenSearch health
curl http://localhost:9200/_cluster/health

# View OpenSearch logs
docker-compose logs opensearch

# Reset OpenSearch data
docker-compose down
docker volume rm wheelsup_opensearch_data
docker-compose up -d opensearch
```

#### Port Conflicts
```bash
# Check what's using ports
lsof -i :5432  # PostgreSQL
lsof -i :9200  # OpenSearch
lsof -i :3000  # Next.js

# Use alternative ports in docker-compose.override.yml
```

#### Node.js/Python Version Issues
```bash
# Check versions
node --version    # Should be 22.x.x
python --version  # Should be 3.14.x

# Use nvm for Node.js version management
nvm use 22
```

### Performance Optimization

#### Database Queries
- Use `EXPLAIN ANALYZE` to identify slow queries
- Ensure proper indexing on frequently queried columns
- Use connection pooling for production workloads

#### API Performance
- Implement proper caching headers
- Use database indexes for filtered queries
- Consider pagination limits to prevent large result sets

#### Memory Usage
- Monitor Docker container memory usage
- Adjust OpenSearch JVM settings for local development
- Close database connections properly

## Contributing

1. Follow the development workflow outlined above
2. Use the task list in `docs/architecture/WheelsUp_MVP_Task_List.md`
3. Update memory bank files in `docs/memory/` for significant changes
4. Ensure all code follows the established patterns and standards

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Drizzle ORM Guide](https://orm.drizzle.team)
- [OpenSearch Documentation](https://opensearch.org/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)

---

**WheelsUp Development Guide** - Complete and up-to-date as of November 2025.
