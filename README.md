# 💧 Water & Operational Efficiency Analytics Dashboard

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-00758F.svg?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Power BI](https://img.shields.io/badge/Power_BI-Desktop-F2C811.svg?logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458.svg?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-D71F00.svg)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **An end-to-end Business Intelligence solution** modeling industrial water consumption, treatment compliance, energy usage, and operational costs across 8 manufacturing facilities.  
> Features an automated Python ETL pipeline, a 3NF/Star Schema MySQL warehouse, 12 business SQL queries, and an interactive 4-page Power BI executive dashboard.

---

## 📌 Executive Summary

Industrial facilities face rising water tariffs, strict wastewater compliance, and aggressive corporate sustainability mandates. This project builds a complete analytics infrastructure to monitor resource efficiency, detect compliance anomalies, and isolate cost inefficiencies.

### 🎯 Key Outcomes & Impact
* **₹11–17 Lakhs Estimated Annual Savings**: Identified through cluster benchmarking, isolating plant P004 (Aurangabad East) consuming 25% more water per unit.
* **Monsoon Seasonality Detection**: Uncovered a 67% spike in water turbidity and quality violations during monsoon months (June–September).
* **Automated Data Quality & Pipeline**: 85 automated data quality tests validating completeness, referential integrity, and sensor range boundaries.
* **Executive Decision Support**: 4 interactive reporting pages in Power BI designed with custom corporate themes and DAX time-intelligence metrics.

---

## 🏗️ Architecture & Data Flow

```text
       [ SENSOR & OPERATIONAL LOGS ]
       (Water, Quality, Energy, Production, Costs)
                     │
                     ▼
       ┌───────────────────────────────┐
       │   Python ETL & Validation     │
       │   (src/etl.py, validation.py) │
       │   • Deduplication & Cleaning  │
       │   • 85 Data Quality Checks    │
       │   • Feature Engineering       │
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │   MySQL Star Schema Warehouse │
       │   (Database: ecolab_analytics)│
       │   • 2 Dimension Tables        │
       │   • 5 Fact Tables             │
       │   • 3 Pre-Aggregated Views    │
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │   Analytics & Visualization   │
       │   • 12 Advanced SQL Queries   │
       │   • 4-Page Power BI Dashboard │
       │   • DAX Executive KPIs        │
       └───────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Domain | Tool / Library | Role in Project |
| :--- | :--- | :--- |
| **Data Engineering** | Python, Pandas, NumPy | Synthetic generation, cleaning, deduplication, feature engineering |
| **Data Quality** | Custom Validation Engine | 85 automated checks (uniqueness, ranges, nulls, foreign keys) |
| **Database** | MySQL 8.0, SQLAlchemy, PyMySQL | Star-schema data warehouse with relational constraints and views |
| **BI & Analytics** | SQL (MySQL Dialect) | CTEs, Window functions (`RANK()`, `LAG()`), Grouping sets |
| **Visualization** | Power BI Desktop | 4-page interactive reporting suite with drill-downs and cross-filtering |
| **Calculations** | DAX (Data Analysis Expressions) | Time-intelligence (MoM), resource ratios, compliance scoring |
| **UI Design** | Custom JSON Palette | Executive Ecolab-inspired theme (Navy, Cyan, Eco-Green) |

---

## 📊 Star Schema Data Model

The data warehouse follows a dimensional **Star Schema** optimized for high-performance aggregation:

```text
                      ┌──────────────────────┐
                      │      dim_date        │
                      │ ──────────────────── │
                      │ PK: date_key         │
                      │     year, month, ... │
                      └──────────┬───────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │ (1:N)                 │ (1:N)                 │ (1:N)
         ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ fact_water_usage │    │fact_water_quality│    │   fact_energy    │
│ ──────────────── │    │ ──────────────── │    │ ──────────────── │
│ FK: date         │    │ FK: date         │    │ FK: date         │
│ FK: plant_id     │    │ FK: plant_id     │    │ FK: plant_id     │
│ water_consumed   │    │ ph, turbidity    │    │ energy_kwh       │
│ recycled_water   │    │ quality_status   │    └────────▲─────────┘
└────────▲─────────┘    └────────▲─────────┘             │
         │ (N:1)                 │ (N:1)                 │ (N:1)
         └───────────────────────┼───────────────────────┘
                                 │
                      ┌──────────┴───────────┐
                      │      dim_plant       │
                      │ ──────────────────── │
                      │ PK: plant_id         │
                      │     plant_name       │
                      │     location, type   │
                      └──────────┬───────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         │ (1:N)                                         │ (1:N)
         ▼                                               ▼
┌──────────────────┐                            ┌──────────────────┐
│ fact_production  │                            │    fact_cost     │
│ ──────────────── │                            │ ──────────────── │
│ FK: date         │                            │ FK: date         │
│ FK: plant_id     │                            │ FK: plant_id     │
│ production_units │                            │ water_cost_inr   │
│ is_downtime      │                            │ energy_cost_inr  │
└──────────────────┘                            │ total_cost_inr   │
                                                └──────────────────┘
```

---

## 📈 Power BI Dashboard Pages

The interactive dashboard ([`powerbi/Dashboard.pbix`](powerbi/Dashboard.pbix)) is organized into 4 strategic pages:

### 1. 🏢 Executive Overview
* **KPI Header Cards**: Total Water Consumed (161.06 ML), Total Cost (₹41.57M), Fleet Recycling Rate (32.3%), and Energy Consumption (4.53M kWh).
* **Plant Water Consumption**: Clustered column chart highlighting Aurangabad East (24.75 ML) as the primary consumer.
* **Monthly Water Consumption Trend**: Chronological time-series showing summer peak (May ~16.9 ML) to winter reduction (~11.7 ML).
* **Interactive Plant Slicer**: Dynamic dropdown filtering all metrics across individual facilities.

### 2. ⚙️ Plant Performance & Benchmarking
* **Unit Cost Comparison**: Horizontal bar chart evaluating cost per production unit across all 8 facilities (ranging from Mumbai West at ₹17.82 to Solapur South at ₹22.26).
* **Plant Performance Scorecard**: Matrix view comparing facility types, water intensity, recycling %, and critical incident counts.

### 3. 🧪 Water Quality & Environmental Compliance
* **Compliance Incident Log**: Detailed table highlighting parameter violations with traffic-light conditional formatting (Critical vs. Warning).
* **Dual-Axis Quality Trend**: Time series plotting pH stability against Turbidity (NTU), clearly exposing the monsoon runoff turbidity spike.
* **Severity Filter**: Fast triage slicer isolating Critical vs. Warning events.

### 4. 🌿 Sustainability Metrics & Cost Structure
* **Recycling Efficiency Trend**: Area chart tracking recycling rates across quarters.
* **Cost Structure by Facility**: 100% stacked bar chart dissecting the ratio of Water Tariffs vs. Electricity vs. Chemical Treatment costs per plant.
* **Production Unit Cost Trend**: Historical tracking of operational expenditure per manufactured unit.

---

## 💡 Key Business Insights & Analytical Findings

Comprehensive details available in [`reports/business_insights.md`](reports/business_insights.md) and [`reports/sql_query_results.md`](reports/sql_query_results.md):

1. **Plant P004 (Aurangabad East) Outlier Analysis**:
   * Consumes **24.75 ML** of water annually vs. the 19.5 ML peer average (**+25% excess**).
   * Generates **342 Critical quality incidents** due to equipment age and inadequate pre-treatment filtration.
   * Resolving P004 leakages and valve calibration provides an immediate **₹6.2 Lakhs annual savings**.
2. **Monsoon Turbidity Shock**:
   * Turbidity levels surge from **3.8 NTU in May to 6.2 NTU in July/August**.
   * Chemical coagulant consumption spikes by 45% during Q3 to maintain regulatory discharge limits.
3. **Power-to-Water Cost Sensitivity**:
   * Energy accounts for **~65–70% of total plant operational spend**.
   * Aeration tank blowers in biological wastewater treatment account for the single largest energy drain.

---

## 📂 Repository Structure

```text
├── data/
│   ├── raw/                      # 6 synthetic operational raw CSVs (with realistic noise)
│   └── processed/                # 7 cleaned tables + master_fact.csv
│
├── powerbi/
│   ├── Dashboard.pbix            # Complete 4-page Power BI dashboard
│   ├── ecolab_executive_theme.json # Corporate executive palette & styling
│   ├── dax_measures.dax          # Library of 25+ DAX calculations
│   ├── powerbi_step_by_step.md   # Step-by-step layout & visual mapping guide
│   └── visual_styling_guide.md   # Formatting tips & aesthetic rules
│
├── reports/
│   ├── business_insights.md      # Executive findings & ROI financial models
│   ├── data_quality_report.csv   # Automated audit log of 85 validation checks
│   └── sql_query_results.md      # Live query outputs & markdown tables for all 12 queries
│
├── sql/
│   ├── schema.sql                # Star schema DDL with primary/foreign keys
│   ├── views.sql                 # 3 analytical views for reporting
│   └── analysis.sql              # 12 business analytical queries (CTEs, Window functions)
│
├── src/
│   ├── generate_data.py          # Synthetic operational data generator
│   ├── etl.py                    # Cleaning, outlier handling, and feature engineering
│   ├── validation.py             # 85-rule data quality test engine
│   ├── load_sql.py               # Automated MySQL warehouse loader
│   └── run_sql_analysis.py       # SQL query execution and report generator
│
├── .env.example                  # Database credential template
├── .gitignore                    # Prevents secret and cache tracking
├── README.md                     # Comprehensive project documentation
├── requirements.txt              # Python library dependencies
└── run_pipeline.py               # One-command end-to-end automation pipeline
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* Python 3.10+
* MySQL Server 8.0+
* Microsoft Power BI Desktop

### 2. Clone & Install Dependencies
```bash
git clone https://github.com/YOUR_USERNAME/water-operational-analytics.git
cd water-operational-analytics
pip install -r requirements.txt
```

### 3. Database Setup
Create your local environment configuration:
```bash
cp .env.example .env
```
Edit `.env` with your MySQL credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ecolab_analytics
DB_USER=root
DB_PASSWORD=your_password
```

### 4. Run the End-to-End Pipeline
Execute the master automation script:
```bash
# Full pipeline: Data Generation -> ETL -> Validation -> MySQL Load
python run_pipeline.py

# Optional: Run without MySQL (CSV generation and cleaning only)
python run_pipeline.py --skip-sql
```

### 5. Open Dashboard
* Launch **Microsoft Power BI Desktop**.
* Open [`powerbi/Dashboard.pbix`](powerbi/Dashboard.pbix).
* If prompted, enter your MySQL root credentials or refresh directly!

---

## 💼 Interview Talking Points

* **Data Engineering & Automation**: *"I built an end-to-end pipeline in Python that generates realistic industrial operational data, executes 85 automated data quality checks, and loads a dimensional star schema into MySQL."*
* **SQL Mastery**: *"I wrote 12 business intelligence queries utilizing CTEs, window functions (`RANK()`, `LAG()`), and views to calculate moving averages, cost intensity, and regulatory violations."*
* **Business Acumen & ROI**: *"Rather than just displaying data, the dashboard uncovered that facility P004 is an outlier with 25% higher water intensity, formulating a tangible ₹11–17 Lakh annual cost reduction strategy."*

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
