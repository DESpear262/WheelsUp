# WheelsUp - Flight School Marketplace MVP

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

WheelsUp aims to become the authoritative, student-first marketplace for flight training — the *Zillow of flight schools* — by aggregating, normalizing, and verifying opaque flight school data.

## Overview

The **MVP** delivers the project's foundational slice: a one-time crawl, extraction, and presentation of flight school data that demonstrates trusted comparability and a scalable technical architecture.

### Key Features
- **Flight School Search**: Search and filter flight schools by location, training type, cost, and VA eligibility
- **Data Transparency**: Every displayed field shows provenance, freshness, and confidence
- **Interactive Maps**: Visualize school locations with Mapbox GL JS
- **Comparison Tools**: Side-by-side comparison of training programs and costs

## Architecture

```
[Source Discovery]
   ↓
[Crawl Layer: Scrapy + Playwright]
   → Raw HTML/PDF/UGC → S3 (raw/)
   ↓
[Text Extraction + Cleaning]
   ↓
[LLM Extraction Layer]
   → JSON (schema-aligned)
   ↓
[Validation + Normalization]
   ↓
[Postgres (RDS + PostGIS)] ←→ [OpenSearch Service]
   ↓
[Next.js Web App (EC2) ←→ RDS + OpenSearch]
```

## Tech Stack

### Frontend
- **Framework**: Next.js 15.0.3
- **Language**: TypeScript 5.6
- **Styling**: Tailwind CSS 3.4 + shadcn/ui
- **Mapping**: Mapbox GL JS 3.3
- **ORM**: Drizzle ORM 0.33

### Backend & ETL
- **Runtime**: Node.js 22 LTS, Python 3.14
- **Database**: PostgreSQL 16 with PostGIS 3.4
- **Search**: Amazon OpenSearch Service 2.13
- **Crawling**: Scrapy 2.12 + Playwright 1.48
- **LLM**: Claude 3.5 Sonnet (primary), GPT-4o (fallback)
- **Validation**: Pydantic 3.0

### Infrastructure
- **Cloud**: AWS (EC2, RDS, OpenSearch, S3, VPC)
- **IaC**: Terraform 1.10+
- **Containers**: Docker + Docker Compose

## Project Structure

```
wheelsup/
├── apps/                 # Application code
│   └── web/             # Next.js frontend
├── etl/                 # ETL pipeline
├── infra/               # Infrastructure as Code
│   └── terraform/       # AWS infrastructure
├── docs/                # Documentation
│   ├── architecture/    # Technical specifications
│   └── memory/         # Implementation knowledge
├── .cursor/             # Agent coordination rules
├── docker-compose.yml   # Local development
└── README.md
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 22 LTS
- Python 3.14
- AWS CLI (configured)

### Local Development Setup

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd wheelsup
   ```

2. **Environment variables**:
   ```bash
   cp apps/web/.env.example apps/web/.env
   cp etl/.env.example etl/.env
   # Edit .env files with your configuration
   ```

3. **Start development environment**:
   ```bash
   docker-compose up -d
   ```

4. **Install dependencies**:
   ```bash
   # Frontend
   cd apps/web
   npm install

   # ETL
   cd ../../etl
   pip install -r requirements.txt
   ```

5. **Run development servers**:
   ```bash
   # Frontend (from apps/web/)
   npm run dev

   # ETL pipeline (from etl/)
   python run_etl.py --snapshot 2025Q1-MVP
   ```

## Development Workflow

### Code Quality
- **Linting**: ESLint for JavaScript/TypeScript, Ruff for Python
- **Formatting**: Prettier for frontend, Black for Python
- **Testing**: Jest for frontend, pytest for ETL

### Commit Guidelines
- Use conventional commits
- Reference PR numbers in commit messages
- Keep commits focused and atomic

### Multi-Agent Coordination
This project uses coordinated AI agents. See `.cursor/rules/` for workflow guidelines.

## Data Sources

- FAA public flight school data
- Official flight school websites
- Flight training directories
- Google Business metadata
- Community discussions (read-only, minimal text)

## Data Provenance

Every field includes:
- `source_type`: Origin (website, directory, reddit, manual)
- `source_url`: Original URL
- `as_of`: Extraction timestamp
- `confidence`: 0–1 numeric confidence score
- `extractor_version`: Pipeline version
- `snapshot_id`: ETL run identifier

## Success Metrics (MVP)

| Category | KPI | Target |
|----------|-----|--------|
| Coverage | Schools indexed | ≥ 1,000 U.S. schools |
| Completeness | Cost + duration fields filled | ≥ 70% |
| Extraction Accuracy | Mean field confidence | ≥ 0.8 |
| Pipeline Reliability | ETL completion without error | 100% |
| Frontend Performance | Search load (p95) | < 2.5s |
| User Conversion | Profile click rate | ≥ 30% |
| Transparency | Fields with "as-of" metadata | 100% |

## Contributing

1. Follow the [development workflow](#development-workflow)
2. Use the task list in `docs/architecture/WheelsUp_MVP_Task_List.md`
3. Update memory bank files in `docs/memory/` for significant changes
4. Ensure all code follows the established patterns

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Roadmap

- **Post-MVP**: Continuous ETL with diff detection
- **Future**: AI concierge, school verification flows, payment integration

---

**WheelsUp MVP** - Building the future of flight training discovery.
