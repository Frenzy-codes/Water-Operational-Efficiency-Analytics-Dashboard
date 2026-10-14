"""
load_sql.py
-----------------------------------------------------------------------------
Water & Operational Efficiency Analytics Dashboard
Phase 5: Load cleaned data into MySQL (Star Schema)

Schema:
  dim_plant       — Plant dimension
  dim_date        — Date dimension (calendar)
  fact_water_usage
  fact_water_quality
  fact_energy
  fact_production
  fact_cost

Uses SQLAlchemy + PyMySQL. Reads credentials from .env file.
-----------------------------------------------------------------------------
"""

import sys
import io
# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

try:
    from sqlalchemy import create_engine, text
    from dotenv import load_dotenv
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

PROC_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
SQL_DIR  = Path(__file__).resolve().parent.parent / "sql"

# -----------------------------------------------------------------------------
# Database connection
# -----------------------------------------------------------------------------
def get_engine():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    host     = os.getenv("DB_HOST", "localhost")
    port     = os.getenv("DB_PORT", "3306")
    db       = os.getenv("DB_NAME", "ecolab_analytics")
    user     = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")

    conn_str = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(conn_str, echo=False)
    return engine


# -----------------------------------------------------------------------------
# Create database if not exists
# -----------------------------------------------------------------------------
def create_database():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    host     = os.getenv("DB_HOST", "localhost")
    port     = os.getenv("DB_PORT", "3306")
    db       = os.getenv("DB_NAME", "ecolab_analytics")
    user     = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")

    # Connect without specifying db first
    root_conn = f"mysql+pymysql://{user}:{password}@{host}:{port}"
    engine = create_engine(root_conn, echo=False)
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db}` DEFAULT CHARACTER SET utf8mb4;"))
        conn.commit()
    print(f"  [OK] Database '{db}' created / verified")


# -----------------------------------------------------------------------------
# Dim: dim_date
# -----------------------------------------------------------------------------
def build_dim_date() -> pd.DataFrame:
    dates = pd.date_range(start="2026-01-01", end="2026-12-31", freq="D")
    df = pd.DataFrame({
        "date_key":    dates.date,
        "year":        dates.year,
        "month":       dates.month,
        "month_name":  dates.strftime("%B"),
        "quarter":     dates.quarter,
        "day_of_week": dates.strftime("%A"),
        "is_weekend":  (dates.dayofweek >= 5).astype(int),
        "week_of_year": dates.isocalendar().week.astype(int),
    })
    return df


# -----------------------------------------------------------------------------
# Load helpers
# -----------------------------------------------------------------------------
def load_table(df: pd.DataFrame, table_name: str, engine, if_exists: str = "replace"):
    df.to_sql(table_name, con=engine, if_exists=if_exists, index=False, chunksize=1000)
    print(f"  [OK] {table_name:<25} -> {len(df):,} rows loaded")


def prepare_fact(csv_name: str, cols: list[str]) -> pd.DataFrame:
    df = pd.read_csv(PROC_DIR / csv_name, parse_dates=["date"])
    # Keep only needed columns
    df = df[[c for c in cols if c in df.columns]].copy()
    df["date"] = df["date"].dt.date  # convert to date for MySQL DATE type
    return df


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("  PHASE 5 — Loading Data into MySQL")
    print("=" * 60)

    if not HAS_DEPS:
        print("  [ERROR] Required packages missing. Run: pip install sqlalchemy pymysql python-dotenv")
        return

    # 1. Create DB
    try:
        create_database()
        engine = get_engine()
    except Exception as e:
        print(f"\n  [ERROR] Database connection failed: {e}")
        print("\n  📝 Make sure your .env file has correct MySQL credentials.")
        print("     Copy .env.example -> .env and fill in your password.\n")
        return

    # 2. Dimension tables
    print("\n  Loading dimension tables...")

    plants = pd.read_csv(PROC_DIR / "plants_clean.csv")
    load_table(plants, "dim_plant", engine)

    dim_date = build_dim_date()
    load_table(dim_date, "dim_date", engine)

    # 3. Fact tables
    print("\n  Loading fact tables...")

    fact_water = prepare_fact("water_usage_clean.csv", [
        "date", "plant_id",
        "water_consumption_liters", "recycled_water_liters",
        "recycling_percentage", "net_water_liters",
    ])
    load_table(fact_water, "fact_water_usage", engine)

    fact_quality = prepare_fact("water_quality_clean.csv", [
        "date", "plant_id",
        "ph", "turbidity_ntu", "tds_ppm", "quality_status",
    ])
    load_table(fact_quality, "fact_water_quality", engine)

    fact_energy = prepare_fact("energy_usage_clean.csv", [
        "date", "plant_id", "energy_kwh",
    ])
    load_table(fact_energy, "fact_energy", engine)

    fact_prod = prepare_fact("production_clean.csv", [
        "date", "plant_id", "production_units", "is_downtime",
    ])
    load_table(fact_prod, "fact_production", engine)

    fact_cost = prepare_fact("costs_clean.csv", [
        "date", "plant_id",
        "water_cost_inr", "energy_cost_inr", "treatment_cost_inr",
        "total_cost_inr", "cost_per_unit", "cost_per_kl",
    ])
    load_table(fact_cost, "fact_cost", engine)

    # 4. Verification
    print("\n  Verifying row counts...")
    tables = [
        "dim_plant", "dim_date",
        "fact_water_usage", "fact_water_quality",
        "fact_energy", "fact_production", "fact_cost",
    ]
    with engine.connect() as conn:
        for tbl in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM `{tbl}`"))
            count  = result.scalar()
            print(f"    {tbl:<30} : {count:,} rows")

    print(f"\n  ✅ All tables loaded into MySQL database 'ecolab_analytics'\n")
    print("  📊 Next: Open Power BI Desktop -> Get Data -> MySQL Database")
    print("     Server: localhost | Database: ecolab_analytics\n")


if __name__ == "__main__":
    main()
