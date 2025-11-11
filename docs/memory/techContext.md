# Technology Stack & Context

## Core Technologies (MVP)
- **Frontend**: Next.js 15.0.3, TypeScript 5.6, Tailwind CSS 3.4, shadcn/ui 0.8
- **Backend**: Node.js 22 LTS, Drizzle ORM 0.33
- **Database**: PostgreSQL 16 (RDS) with PostGIS 3.4
- **Search**: Amazon OpenSearch Service 2.13
- **ETL**: Python 3.14, Scrapy 2.12, Playwright 1.48
- **LLM**: Claude 3.5 Sonnet (AWS Bedrock), GPT-4o (OpenAI API fallback)
- **Validation**: Pydantic 3.0
- **Text Processing**: trafilatura 1.9.0, pdfminer.six 20241015
- **Infrastructure**: AWS (EC2 t3.large, VPC, ALB, CloudFront, S3, Secrets Manager)

## Development Environment
- **Local Development**: Docker Compose with Node.js and Python containers
- **Code Quality**: ESLint, Prettier, Black, Ruff
- **Version Control**: Git with structured commit messages
- **Documentation**: Markdown files in docs/ directory

## Current Setup Status
- Repository structure not yet initialized
- No Docker environment configured
- No package.json or requirements.txt created
- No linting/formatting tools configured

## Dependencies to Install
### Frontend (apps/web/)
- next@15.0.3
- react
- typescript@5.6
- tailwindcss@3.4
- @shadcn/ui@0.8
- drizzle-orm@0.33
- mapbox-gl@3.3 (for mapping)

### ETL (etl/)
- python@3.14
- scrapy@2.12
- playwright@1.48
- pydantic@3.0
- trafilatura@1.9.0
- pdfminer.six@20241015
- boto3 (AWS SDK)
- anthropic (Claude API)

### Infrastructure
- terraform@1.10+
- awscli

## Known Constraints
- Must comply with robots.txt and data licensing restrictions
- LLM API costs need monitoring and optimization
- Data extraction accuracy targets: ≥70% field completeness, ≥0.8 confidence
