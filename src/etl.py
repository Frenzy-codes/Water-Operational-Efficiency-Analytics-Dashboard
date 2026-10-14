"""
etl.py
-----------------------------------------------------------------------------
Water & Operational Efficiency Analytics Dashboard
Phase 3: ETL — Data Cleaning & Transformation

Simulates receiving "dirty" operational data from multiple business systems.
Performs:
  1. Load all raw CSVs
  2. Convert date columns -> datetime
  3. Remove duplicate rows (logged)
  4. Fill / drop missing values (logged)
  5. Clip invalid negatives to 0
  6. Cap recycling % at 100
  7. Add derived / calculated columns
  8. Save cleaned files to data/processed/
-----------------------------------------------------------------------------
"""

import sys
import io
# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR  = Path(__file__).resolve().parent.parent / "data" / "raw"
PROC_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

# -- Logging helper ------------------------------------------------------------
ETL_LOG: list[dict] = []

def log(dataset: str, step: str, detail: str, records: int = 0):
    ETL_LOG.append({"dataset": dataset, "step": step, "detail": detail, "records_affected": records})
    tag = "[WARN]️ " if records > 0 else "  "
    print(f"  {tag} [{dataset}] {step}: {detail} ({records} records)")


# -----------------------------------------------------------------------------
# Shared cleaning utilities
# -----------------------------------------------------------------------------
def _drop_duplicates(df: pd.DataFrame, name: str, subset: list[str]) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=subset)
    dropped = before - len(df)
    log(name, "Duplicate removal", f"Dropped {dropped} duplicate rows", dropped)
    return df


def _fill_missing_numeric(df: pd.DataFrame, name: str, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        missing = df[col].isnull().sum()
        if missing > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            log(name, "Missing value fill", f"Column '{col}' filled {missing} NaNs with median ({median_val:.1f})", missing)
    return df


def _clip_negatives(df: pd.DataFrame, name: str, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            df[col] = df[col].clip(lower=0)
            log(name, "Negative clip", f"Column '{col}' clipped {neg_count} negative values to 0", neg_count)
    return df


# -----------------------------------------------------------------------------
# 1. plants.csv  ->  plants_clean.csv
# -----------------------------------------------------------------------------
def clean_plants() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "plants.csv")
    log("plants", "Load", f"Loaded {len(df)} rows")
    df = _drop_duplicates(df, "plants", subset=["plant_id"])
    df["plant_name"] = df["plant_name"].str.strip()
    df["location"]   = df["location"].str.strip()
    df["plant_type"] = df["plant_type"].str.strip()
    df.to_csv(PROC_DIR / "plants_clean.csv", index=False)
    print(f"  [OK] plants_clean.csv saved -> {len(df)} rows")
    return df


# -----------------------------------------------------------------------------
# 2. water_usage.csv  ->  water_usage_clean.csv
# -----------------------------------------------------------------------------
def clean_water_usage() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "water_usage.csv")
    log("water_usage", "Load", f"Loaded {len(df)} rows")

    df["date"] = pd.to_datetime(df["date"])
    df = _drop_duplicates(df, "water_usage", subset=["date", "plant_id"])
    df = _fill_missing_numeric(df, "water_usage", ["water_consumption_liters", "recycled_water_liters"])
    df = _clip_negatives(df, "water_usage", ["water_consumption_liters", "recycled_water_liters"])

    # Derived columns
    df["recycling_percentage"] = (
        df["recycled_water_liters"] / df["water_consumption_liters"] * 100
    ).round(2)

    # Cap recycling at 100% (data integrity)
    overcapped = (df["recycling_percentage"] > 100).sum()
    if overcapped:
        df["recycling_percentage"] = df["recycling_percentage"].clip(upper=100)
        log("water_usage", "Recycling cap", f"Capped {overcapped} rows where recycling > 100%", overcapped)

    df["net_water_liters"] = (df["water_consumption_liters"] - df["recycled_water_liters"]).round(0)
    df["month"]            = df["date"].dt.month
    df["month_name"]       = df["date"].dt.strftime("%B")
    df["quarter"]          = df["date"].dt.quarter
    df["year"]             = df["date"].dt.year
    df["day_of_week"]      = df["date"].dt.strftime("%A")

    df.sort_values(["date", "plant_id"], inplace=True)
    df.to_csv(PROC_DIR / "water_usage_clean.csv", index=False)
    print(f"  [OK] water_usage_clean.csv saved -> {len(df)} rows")
    return df


# -----------------------------------------------------------------------------
# 3. water_quality.csv  ->  water_quality_clean.csv
# -----------------------------------------------------------------------------
def clean_water_quality() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "water_quality.csv")
    log("water_quality", "Load", f"Loaded {len(df)} rows")

    df["date"] = pd.to_datetime(df["date"])
    df = _drop_duplicates(df, "water_quality", subset=["date", "plant_id"])
    df = _fill_missing_numeric(df, "water_quality", ["ph", "turbidity_ntu", "tds_ppm"])

    # Physical bounds validation
    invalid_ph = ((df["ph"] < 0) | (df["ph"] > 14)).sum()
    if invalid_ph:
        df = df[(df["ph"] >= 0) & (df["ph"] <= 14)]
        log("water_quality", "pH bound drop", f"Dropped {invalid_ph} rows with pH outside [0,14]", invalid_ph)

    df["turbidity_ntu"] = df["turbidity_ntu"].clip(lower=0)
    df["tds_ppm"]       = df["tds_ppm"].clip(lower=0)

    # Recalculate quality_status based on validated readings
    def classify(row):
        if row["ph"] < 5.5 or row["ph"] > 9.5 or row["turbidity_ntu"] > 10 or row["tds_ppm"] > 1000:
            return "Critical"
        elif row["ph"] < 6.5 or row["ph"] > 8.5 or row["turbidity_ntu"] > 5 or row["tds_ppm"] > 500:
            return "Warning"
        return "Normal"

    df["quality_status"] = df.apply(classify, axis=1)

    df["month"]      = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["quarter"]    = df["date"].dt.quarter
    df["year"]       = df["date"].dt.year

    df.sort_values(["date", "plant_id"], inplace=True)
    df.to_csv(PROC_DIR / "water_quality_clean.csv", index=False)
    print(f"  [OK] water_quality_clean.csv saved -> {len(df)} rows")
    return df


# -----------------------------------------------------------------------------
# 4. energy_usage.csv  ->  energy_usage_clean.csv
# -----------------------------------------------------------------------------
def clean_energy_usage() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "energy_usage.csv")
    log("energy_usage", "Load", f"Loaded {len(df)} rows")

    df["date"] = pd.to_datetime(df["date"])
    df = _drop_duplicates(df, "energy_usage", subset=["date", "plant_id"])
    df = _fill_missing_numeric(df, "energy_usage", ["energy_kwh"])
    df = _clip_negatives(df, "energy_usage", ["energy_kwh"])

    df["month"]      = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["quarter"]    = df["date"].dt.quarter
    df["year"]       = df["date"].dt.year

    df.sort_values(["date", "plant_id"], inplace=True)
    df.to_csv(PROC_DIR / "energy_usage_clean.csv", index=False)
    print(f"  [OK] energy_usage_clean.csv saved -> {len(df)} rows")
    return df


# -----------------------------------------------------------------------------
# 5. production.csv  ->  production_clean.csv
# -----------------------------------------------------------------------------
def clean_production() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "production.csv")
    log("production", "Load", f"Loaded {len(df)} rows")

    df["date"] = pd.to_datetime(df["date"])
    df = _drop_duplicates(df, "production", subset=["date", "plant_id"])
    df = _fill_missing_numeric(df, "production", ["production_units"])
    df = _clip_negatives(df, "production", ["production_units"])

    # Flag downtime days
    df["is_downtime"] = (df["production_units"] == 0).astype(int)
    downtime_count = df["is_downtime"].sum()
    log("production", "Downtime flag", f"Flagged {downtime_count} downtime days", downtime_count)

    df["month"]      = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["quarter"]    = df["date"].dt.quarter
    df["year"]       = df["date"].dt.year

    df.sort_values(["date", "plant_id"], inplace=True)
    df.to_csv(PROC_DIR / "production_clean.csv", index=False)
    print(f"  [OK] production_clean.csv saved -> {len(df)} rows")
    return df


# -----------------------------------------------------------------------------
# 6. costs.csv  ->  costs_clean.csv
# -----------------------------------------------------------------------------
def clean_costs(water_df: pd.DataFrame, energy_df: pd.DataFrame, production_df: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "costs.csv")
    log("costs", "Load", f"Loaded {len(df)} rows")

    df["date"] = pd.to_datetime(df["date"])
    df = _drop_duplicates(df, "costs", subset=["date", "plant_id"])
    df = _fill_missing_numeric(df, "costs", ["water_cost_inr", "energy_cost_inr", "treatment_cost_inr"])
    df = _clip_negatives(df, "costs", ["water_cost_inr", "energy_cost_inr", "treatment_cost_inr"])

    # Derived: total cost
    df["total_cost_inr"] = (
        df["water_cost_inr"] + df["energy_cost_inr"] + df["treatment_cost_inr"]
    ).round(2)

    # Merge production to compute cost per unit
    prod = production_df[["date", "plant_id", "production_units"]].copy()
    prod["date"] = pd.to_datetime(prod["date"])
    df = df.merge(prod, on=["date", "plant_id"], how="left")
    df["cost_per_unit"] = np.where(
        df["production_units"] > 0,
        (df["total_cost_inr"] / df["production_units"]).round(4),
        np.nan,
    )

    # Merge water consumption to compute water cost per kL
    water = water_df[["date", "plant_id", "water_consumption_liters"]].copy()
    water["date"] = pd.to_datetime(water["date"])
    df = df.merge(water, on=["date", "plant_id"], how="left")
    df["cost_per_kl"] = np.where(
        df["water_consumption_liters"] > 0,
        (df["water_cost_inr"] / (df["water_consumption_liters"] / 1000)).round(4),
        np.nan,
    )

    df["month"]      = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["quarter"]    = df["date"].dt.quarter
    df["year"]       = df["date"].dt.year

    df.sort_values(["date", "plant_id"], inplace=True)

    # Drop helper cols before saving (keep in fact table clean)
    df_save = df.drop(columns=["production_units", "water_consumption_liters"])
    df_save.to_csv(PROC_DIR / "costs_clean.csv", index=False)
    print(f"  [OK] costs_clean.csv saved -> {len(df_save)} rows")
    return df


# -----------------------------------------------------------------------------
# 7. Master fact table  ->  master_fact.csv
# -----------------------------------------------------------------------------
def build_master_fact(water_df, quality_df, energy_df, production_df, costs_df):
    """
    Joins all fact tables into one wide master table for quick Power BI loading
    or Jupyter exploration.
    """
    base = water_df[["date", "plant_id", "water_consumption_liters",
                      "recycled_water_liters", "recycling_percentage",
                      "net_water_liters"]].copy()

    base = base.merge(
        energy_df[["date", "plant_id", "energy_kwh"]], on=["date", "plant_id"], how="left"
    ).merge(
        production_df[["date", "plant_id", "production_units", "is_downtime"]], on=["date", "plant_id"], how="left"
    ).merge(
        costs_df[["date", "plant_id", "water_cost_inr", "energy_cost_inr",
                  "treatment_cost_inr", "total_cost_inr", "cost_per_unit"]], on=["date", "plant_id"], how="left"
    ).merge(
        quality_df[["date", "plant_id", "ph", "turbidity_ntu", "tds_ppm", "quality_status"]], on=["date", "plant_id"], how="left"
    )

    base["month"]      = pd.to_datetime(base["date"]).dt.month
    base["month_name"] = pd.to_datetime(base["date"]).dt.strftime("%B")
    base["quarter"]    = pd.to_datetime(base["date"]).dt.quarter
    base["year"]       = pd.to_datetime(base["date"]).dt.year

    base.to_csv(PROC_DIR / "master_fact.csv", index=False)
    print(f"  [OK] master_fact.csv saved -> {len(base)} rows × {len(base.columns)} cols")
    return base


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("  PHASE 3 — ETL: Cleaning & Transformation")
    print("=" * 60)

    plants_df     = clean_plants()
    water_df      = clean_water_usage()
    quality_df    = clean_water_quality()
    energy_df     = clean_energy_usage()
    production_df = clean_production()
    costs_df      = clean_costs(water_df, energy_df, production_df)

    print("\n  Building master fact table...")
    build_master_fact(water_df, quality_df, energy_df, production_df, costs_df)

    print(f"\n  📁 Cleaned data saved to: {PROC_DIR}")
    print(f"  📋 ETL log: {len(ETL_LOG)} events recorded\n")
    return {
        "plants": plants_df,
        "water": water_df,
        "quality": quality_df,
        "energy": energy_df,
        "production": production_df,
        "costs": costs_df,
    }


if __name__ == "__main__":
    main()
