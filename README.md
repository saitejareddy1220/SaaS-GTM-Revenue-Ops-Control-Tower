# SaaS GTM Revenue & Ops Control Tower

End-to-end analytics stack demonstrating modern data engineering and analytics best practices

A complete, production-ready analytics platform for B2B SaaS go-to-market organizations. This project showcases synthetic data generation, warehouse modeling with dbt, comprehensive data quality testing, and stakeholder-ready dashboards—all running locally via Docker.

---

## Overview

This control tower provides unified visibility into:
- **Revenue Metrics**: MRR, ARR, NRR, expansion, contraction, churn
- **Pipeline Performance**: Win rates, sales cycle, conversion by segment
- **Product Adoption**: Activation rates, time-to-value, usage patterns
- **Customer Retention**: Cohort analysis, churn drivers, lifetime value
- **Support Quality**: Ticket volume, SLA compliance, resolution times
- **Marketing Efficiency**: CAC by channel, payback periods, ROAS
- **Anomaly Detection**: Automated flagging of significant metric shifts

---

## Architecture

```
┌─────────────────┐
│  Data Generator │  ← Python script (Faker, pandas, numpy)
│  (Synthetic)    │     18 months of realistic SaaS data
└────────┬────────┘
         │ CSVs
         ▼
┌─────────────────┐
│   Postgres DB   │  ← Warehouse (Docker)
│   (raw_* tables)│     9 raw tables loaded via Python
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   dbt Project   │  ← Transformations (staging → marts)
│                 │     9 staging views
│                 │     2 dimension tables
│                 │     7 fact tables
│                 │     20+ schema tests
│                 │     2 custom SQL tests
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Streamlit App  │  ← Dashboard (5 pages)
│  (Analytics UI) │     Executive Overview
│                 │     Funnel & Pipeline
│                 │     Retention & Cohorts
│                 │     Support & Quality
│                 │     Anomalies
└─────────────────┘
```

---

## Dashboard Demo

See the complete 5-page interactive dashboard in action:

https://github.com/saitejareddy1220/SaaS-GTM-Revenue-Ops-Control-Tower/assets/dashboard.mp4

**Dashboard Pages:**
- Executive Overview with KPIs (MRR, ARR, CAC, Activation Rate)
- Pipeline Analytics (Win rates by segment, sales cycle)  
- Cohort Retention Heatmaps (12-month retention tracking)
- Support Metrics (Ticket volume, SLA compliance)
- Anomaly Detection (Automated spike/drop identification)

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Orchestration** | Docker Compose, Makefile | Single-command deployment |
| **Warehouse** | PostgreSQL 15 | Data storage and query engine |
| **Transformation** | dbt 1.10+ | SQL-based data modeling |
| **Visualization** | Streamlit (custom styling) | Interactive dashboards with sky blue theme |
| **Data Generation** | Python (Faker, pandas) | Synthetic SaaS data |
| **Admin** | pgAdmin 4 (optional) | Database inspection |

---

## Prerequisites

- **Docker Desktop** installed and running
- **Python 3.9+** for data generation, loader, and dashboard
- **dbt-core** installed (`pip install dbt-core dbt-postgres`)
- **macOS/Linux** (tested on macOS)

---

## Setup

### 1. Clone and Navigate

```bash
cd ~/Desktop/DA
```

### 2. Environment Configuration

```bash
cp .env.example .env
```

Default credentials work out of the box. Edit `.env` to customize database settings if needed.

### 3. Install Python Dependencies

```bash
# Data generator
pip install -r data_gen/requirements.txt

# Data loader
pip install -r loader/requirements.txt

# Dashboard
pip install -r app/requirements.txt
```

---

## Running the Project

### **Option 1: Full Pipeline (Recommended)**

Run everything in sequence with a single command:

```bash
make all
```

This executes:
1. `make up` → Start Docker containers
2. `make gen-data` → Generate 18 months of synthetic data
3. `make load-data` → Load CSVs into Postgres
4. `make dbt-deps` → Install dbt dependencies
5. `make dbt-run` → Build all staging and mart models
6. `make dbt-test` → Run data quality tests

After completion, launch the dashboard:

```bash
make app
```

The dashboard opens at **http://localhost:8501**

---

### **Option 2: Step-by-Step**

For more control, run each step individually:

```bash
# Start infrastructure
make up

# Generate synthetic data
make gen-data

# Load into warehouse
make load-data

# Run dbt transformations
make dbt-run

# Run data quality tests
make dbt-test

# Launch dashboard
make app
```

---

## Project Structure

```
/Users/saitejareddy/Desktop/DA/
├── docker-compose.yml          # Postgres + pgAdmin containers
├── Makefile                    # Orchestration commands
├── .env                        # Environment configuration
├── .gitignore
│
├── data_gen/
│   ├── generator.py            # Synthetic data generation
│   ├── requirements.txt
│   └── output/                 # Generated CSVs (gitignored)
│
├── loader/
│   ├── load_csv_to_postgres.py # CSV → Postgres loader
│   └── requirements.txt
│
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml            # Database connection profile
│   ├── models/
│   │   ├── staging/            # 9 staging models (views)
│   │   │   ├── sources.yml
│   │   │   ├── schema.yml      # Schema tests
│   │   │   └── stg_*.sql
│   │   └── marts/              # 2 dims + 7 facts (tables)
│   │       ├── schema.yml
│   │       ├── dim_*.sql
│   │       └── fct_*.sql
│   └── tests/                  # Custom SQL tests
│       ├── assert_non_negative_amounts.sql
│       └── assert_valid_subscription_dates.sql
│
├── app/
│   ├── streamlit_app.py        # Multi-page dashboard
│   └── requirements.txt
│
├── README.md                   # This file
└── INSIGHTS.md                 # Executive insights memo
```

---

## Data Model

### **Staging Layer** (`staging` schema)
Clean, renamed, type-cast versions of raw tables:
- `stg_accounts`, `stg_users`, `stg_subscriptions`
- `stg_invoices`, `stg_payments`
- `stg_crm_deals`, `stg_product_events`
- `stg_support_tickets`, `stg_marketing_spend`

### **Marts Layer** (`marts` schema)

**Dimensions:**
- `dim_date` – Calendar dimension
- `dim_account` – Account attributes with current subscription status

**Facts:**
- `fct_revenue_monthly` – MRR/ARR with expansion, contraction, churn, NRR
- `fct_pipeline` – Deal stage conversions, win rates, sales cycle
- `fct_activation` – Activation rates and time-to-activate
- `fct_retention` – Cohort retention curves and churn rates
- `fct_support` – Ticket volume, severity, SLA breach metrics
- `fct_cac_ltv` – CAC and LTV by marketing channel (Google Ads, LinkedIn, Content Marketing, Events, Referral)
- `fct_anomalies` – Month-over-month metric anomalies

---

## Dashboard

Access at **http://localhost:8501** after running `make app`.

**Features:** Modern sky blue theme with custom CSS styling for enhanced visual appeal.

### **Pages**

1. **Executive Overview**
   - KPI cards: MRR, ARR, NRR, Active Accounts, Activation Rate, Avg CAC, Churned MRR
   - MRR trend with new/expansion/churn breakdown
   - Revenue by segment pie chart

2. **Funnel & Pipeline**
   - Win rates by segment
   - Sales cycle analysis
   - Deal value distribution

3. **Retention & Cohorts**
   - Cohort retention heatmap
   - Activation vs retention correlation
   - Churn trends over time

4. **Support & Quality**
   - Ticket volume by segment and severity
   - SLA breach rates by region
   - Resolution time metrics

5. **Anomalies**
   - Automated detection of >10% MoM changes
   - Spike/drop classification
   - Metric trend visualization

### **Global Filters**
Apply segment, region, and acquisition channel (Google Ads, LinkedIn, Content Marketing, Events, Referral) filters via sidebar to slice all dashboards dynamically.

---

## Data Quality

### **Built-in dbt Tests** (20+ tests)
- Primary key uniqueness on all dimensions and facts
- Foreign key relationships between facts and dimensions
- Accepted values for categorical fields (segment, status, severity)
- Not null constraints on critical fields

### **Custom SQL Tests** (2 tests)
1. **No Negative Amounts**: Validates that invoices and MRR are never negative
2. **Valid Subscription Dates**: Ensures `start_date <= end_date` and invoices fall within subscription periods

Run all tests:
```bash
make dbt-test
```

Expected output: All tests pass

---

## Troubleshooting

### **Docker Not Running**
```bash
# Check Docker status
docker ps

# Start Docker Desktop, then:
make up
```

### **Database Connection Failed**
```bash
# Verify Postgres is healthy
docker logs saas_gtm_warehouse

# Restart containers
make down && make up
```

### **dbt Command Not Found**
```bash
pip install dbt-core dbt-postgres
```

### **No Data in Dashboard**
Ensure you've run the full pipeline:
```bash
make all
```

### **Port Conflicts**
Edit `.env` to change ports if 5432, 8080, or 8501 are in use.

---

## Cleanup

Remove generated data and dbt artifacts:
```bash
make clean
```

Stop and remove containers:
```bash
make down
```

---

## License

MIT License - Free to use for learning and portfolio purposes.

