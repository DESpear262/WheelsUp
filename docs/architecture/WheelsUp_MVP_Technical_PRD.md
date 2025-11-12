# Technical Product Requirements Document
### Project: WheelsUp (Flight School Marketplace MVP)
### Version: MVP — One-Shot Scrape → ETL → Present
### Audience: Engineering, Data/ML, Product Management
### Last Updated: November 2025

---

## 1. Overview

### Vision
WheelsUp aims to become the authoritative, student-first marketplace for flight training — the *Zillow of flight schools* — by aggregating, normalizing, and verifying opaque flight school data.  

The **MVP** delivers the project’s foundational slice: a one-time crawl, extraction, and presentation of flight school data that demonstrates trusted comparability and a scalable technical architecture.

### Objective
Deliver a fully functional, reproducible data and web stack that enables:
- End users (students) to search, filter, and compare flight schools.  
- The product and engineering team to run a complete scrape → ETL → publish cycle.  
- Each displayed data field to show **provenance, freshness, and confidence**.

This version establishes the groundwork for continuous data refreshes, trust tiers, and monetization.

---

## 2. Scope (MVP)

| **In Scope** | **Out of Scope** |
|---------------|------------------|
| Crawl public flight school data (directories, websites, Google Places metadata, Reddit where permitted) | Continuous crawl or automatic data refresh |
| Single-run ETL pipeline for extraction, validation, normalization | Partner data (e.g., Flight Schedule Pro) |
| LLM-based schema extraction (price, duration, training type, etc.) | AI concierge or guided comparison |
| Searchable web UI with filters, map view, compare cards | Lead routing, CRM, or payments |
| AWS EC2-hosted stack (frontend, API, DB, search) | Serverless or multi-region deployment |
| Data transparency: provenance, timestamps, confidence | Verified operational metrics (deferred) |

---

## 3. Core User Stories

### For Students
1. I can search for flight schools by city, state, or airport code.  
2. I can filter schools by training type (Part 61/141), cost range, or VA eligibility.  
3. I can compare key stats: expected cost, training duration, fleet, and Google rating.  
4. I can see when data was last verified (“As of”) and its source.  

### For Product & Data Teams
1. I can run a reproducible crawl + ETL job and generate a new dataset snapshot.  
2. I can measure extraction completeness and confidence by field and source.  
3. I can trace any value to its source document or URL.  
4. I can publish a static snapshot to the live site and roll back if needed.  

---

## 4. System Overview

### Architecture Diagram (conceptual)

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

Each full run produces a **snapshot** (e.g., `snapshot_id: "2025Q1-MVP"`) that is immutable and auditable.

---

## 5. Key Components

### 5.1 Data Acquisition
- **Sources:** FAA public data, known flight school directories, official websites, Google Business metadata, Reddit discussions (read-only, minimal text).  
- **Tools:** `Scrapy 2.12`, `Playwright 1.48`  
- **Storage:** S3 (`raw/{snapshot_id}/{source}/{school_id}`)  
- **Metadata:** `crawl_time`, `source_url`, `http_status`, `content_hash`, `content_type`  
- **Deduplication:** by domain, phone, ICAO, and lat/long geohash.  
- **Compliance:** Full respect for `robots.txt` and data licensing restrictions.

### 5.2 Text Extraction & Preprocessing
- **Libraries:** `trafilatura 1.9.0`, `pdfminer.six 20241015`, optional OCR via `pytesseract 0.3.13`.  
- **Outputs:** Clean text with metadata and per-section headers.  
- **Storage:** S3 (`parsed/{snapshot_id}/...`)  

### 5.3 LLM Extraction Layer
- **Runtime:** Python **3.14 (stable)**  
- **Models:**  
  - Primary: **Claude 3.5 Sonnet (AWS Bedrock)**  
  - Fallback: **GPT-4o (OpenAI API)**  
- **Prompt style:**  
  - Strict schema JSON output.  
  - “Abstain” on uncertainty (`value: null`, `confidence: 0.0`).  
  - Field-level provenance (`source_url`, `extractor_version`).  
- **Batching:** Section-aware chunking with content hashing to prevent reprocessing.  
- **Output:** `school_{id}.json` with `fields`, `confidence`, `as_of`.

### 5.4 Validation & Normalization
- **Framework:** `Pydantic 3.0` models.  
- **Logic:**  
  - Convert per-hour rates to total program cost bands.  
  - Validate numeric and enum fields (Part type, VA flag, program duration).  
  - Cross-field checks: total cost ≈ rate × hours ± 20%.  
  - Reject or flag implausible values.  
- **Human Review:**  
  - Sample set of top 50 schools manually verified pre-publication.  
- **Output:** Flattened JSONs inserted into **Postgres** (RDS).  

### 5.5 Data Storage
- **RDS PostgreSQL 16** with **PostGIS 3.4** for geo indexing.  
- **Key tables:** `schools`, `campuses`, `programs`, `pricing`, `metrics`, `reviews`, `attributes`.  
- **Field metadata:** `snapshot_id`, `as_of`, `confidence`, `source_type`, `source_url`.  
- **Search layer:** **Amazon OpenSearch Service 2.13** (geo_point, filter facets, text relevance).  
- **Index versioning:** `schools_v1_{snapshot_id}` → alias `schools_current`.

### 5.6 Web Application
- **Framework:** **Next.js 15.0.3 (stable)**, **TypeScript 5.6**, **Node.js 22 LTS**.  
- **UI:** Tailwind CSS 3.4 + shadcn/ui components.  
- **Data layer:** Drizzle ORM 0.33 with Postgres adapter.  
- **Mapping:** Mapbox GL JS 3.3 for campus visualization.  
- **Search:** OpenSearch SDK with precomputed facets.  
- **Features:**  
  - Filters: location, program, part type, cost, VA eligibility.  
  - Compare cards & profile views with “as of” badges.  
  - “Suggest an Edit” form → S3 queue for moderation.  
- **Deployment:** Dockerized container on EC2 (t3.large) with Nginx reverse proxy, behind ALB + CloudFront.  

### 5.7 Infrastructure & Security
- **Cloud provider:** AWS  
- **Compute:** EC2 (frontend + ETL runners).  
- **Storage:** S3 (raw, parsed, normalized, published, logs).  
- **Database:** RDS Postgres (multi-AZ, daily snapshot).  
- **Search:** OpenSearch (2 data nodes).  
- **Networking:** VPC with public/private subnets; RDS/OpenSearch private only.  
- **TLS & Encryption:** KMS for at-rest; ACM for HTTPS.  
- **Auth:** Cognito (admin access).  
- **Secrets:** AWS Secrets Manager.  
- **Observability:** CloudWatch metrics + Sentry integration.  

---

## 6. Data Provenance & Governance
Every field includes:
| Field | Description |
|-------|--------------|
| `source_type` | Origin (website, directory, reddit, manual) |
| `source_url` | Original URL |
| `as_of` | Extraction timestamp |
| `confidence` | 0–1 numeric confidence |
| `extractor_version` | Semantic version of pipeline |
| `snapshot_id` | Unique ID of ETL run |

All ETL runs are immutable and auditable.

---

## 7. Success Metrics (MVP)

| Category | KPI | Target |
|-----------|-----|--------|
| **Coverage** | Schools indexed | ≥ 1,000 U.S. schools |
| **Completeness** | Cost + duration fields filled | ≥ 70% |
| **Extraction Accuracy** | Mean field confidence | ≥ 0.8 |
| **Pipeline Reliability** | ETL completion without error | 100% |
| **Frontend Performance** | Search load (p95) | < 2.5s |
| **User Conversion Proxy** | Profile click rate | ≥ 30% |
| **Transparency** | % of displayed fields with “as-of” metadata | 100% |

---

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|-------|---------|------------|
| LLM hallucination | False data | Strict schema + abstain enforcement |
| Data duplication | Misleading results | Fuzzy dedupe rules + merge audit |
| Legal violations (scraping) | TOS breach | Obey robots.txt, store metadata only |
| LLM cost spikes | Budget overrun | Hash dedupe, batch prompts |
| Stale data perception | Credibility loss | Prominent “as of” timestamps |
| Security misconfigurations | Data exposure | Private subnet isolation, IAM least privilege |

---

## 9. Deliverables

1. One-shot ETL pipeline executable via CLI (`python run_etl.py --snapshot 2025Q1-MVP`).  
2. Snapshot manifest JSON (sources, counts, timestamps) stored in S3.  
3. Populated Postgres + OpenSearch indices.  
4. Publicly accessible web app deployed on EC2.  
5. Documentation: architecture diagram, data dictionary, runbook, Terraform config.  
6. QA results: coverage and confidence summary report.

---

## 10. Ownership

| Role | Responsibility |
|------|----------------|
| **Product Manager** | Scope, milestones, QA gates, and release tracking |
| **Data Engineer** | Crawl, ETL, validation, publishing |
| **ML Engineer** | Prompt design, LLM orchestration, schema extraction |
| **Backend Engineer** | API design, RDS + OpenSearch integration |
| **Frontend Engineer** | Next.js interface, map integration, UI |
| **DevOps Engineer** | AWS IaC, deployments, monitoring, backups |

---

## 11. Future Roadmap (Post-MVP)

- Continuous ETL with diff detection and freshness scoring.  
- Flight Schedule Pro (FSP) data integration and Trust Tier generation.  
- AI-powered “Training Concierge” recommender.  
- School claim and verification flows.  
- Financing/booking integrations.  
- Public API for partner access.

---

## 12. Technical Appendix — Canonical Stack (MVP)

| Layer | Tool/Service | Version | Purpose |
|--------|---------------|----------|----------|
| **Frontend Framework** | Next.js | 15.0.3 (stable) | SSR/SSG React app |
| **Language (frontend)** | TypeScript | 5.6 | Typed UI + API integration |
| **UI & Styling** | Tailwind CSS / shadcn/ui | 3.4 / 0.8 | Design system |
| **ORM** | Drizzle ORM | 0.33 | Type-safe Postgres access |
| **Backend Runtime** | Node.js | 22 LTS | API routes & server logic |
| **Database** | PostgreSQL | 16 (RDS) | Primary relational store |
| **Geo Extension** | PostGIS | 3.4 | Spatial queries |
| **Search** | Amazon OpenSearch | 2.13 | Faceted + geo search |
| **Crawler** | Scrapy / Playwright | 2.12 / 1.48 | Site crawling & JS rendering |
| **ETL Language** | Python | 3.14 (stable) | Crawling, normalization, LLM integration |
| **Schema Validation** | Pydantic | 3.0 | Data modeling & type enforcement |
| **LLM Integration** | Claude 3.5 Sonnet / GPT-4o | — | Schema extraction |
| **Storage** | Amazon S3 | Latest | Raw & processed artifact storage |
| **Compute** | Amazon EC2 | t3.large / c5.xlarge | Frontend + ETL workloads |
| **Networking** | VPC, ALB, CloudFront | Latest | Public/private separation, caching |
| **Auth** | Amazon Cognito | Latest | Admin access |
| **Secrets** | AWS Secrets Manager | Latest | Key and credential storage |
| **Monitoring** | CloudWatch / Sentry | Latest | Metrics and error tracing |
| **Infrastructure-as-Code** | Terraform | 1.10+ | IaC for all AWS resources |

---

**End of Document — WheelsUp MVP Technical PRD (v1.0)**
