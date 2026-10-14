"""
validation.py
-----------------------------------------------------------------------------
Water & Operational Efficiency Analytics Dashboard
Phase 4: Data Quality Validation

Runs structured validation rules against the CLEANED datasets and produces:
  - reports/data_quality_report.csv  (machine-readable)
  - Console summary (human-readable)

Validation categories:
  1. Completeness  — no missing values
  2. Uniqueness    — no duplicate keys
  3. Range         — numeric values within business-defined thresholds
  4. Referential   — all fact plant_ids exist in dim_plant
  5. Consistency   — derived column logic (e.g. recycling_pct <= 100)
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
from datetime import datetime

PROC_DIR    = Path(__file__).resolve().parent.parent / "data" / "processed"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# -- Business-defined acceptable ranges --------------------------------------
RANGES = {
    "water_usage_clean": {
        "water_consumption_liters": (1_000,   200_000),
        "recycled_water_liters":    (0,        None),
        "recycling_percentage":     (0,        100),
        "net_water_liters":         (0,        None),
    },
    "water_quality_clean": {
        "ph":            (0,    14),
        "turbidity_ntu": (0,    50),
        "tds_ppm":       (0,    2000),
    },
    "energy_usage_clean": {
        "energy_kwh": (0, 10_000),
    },
    "production_clean": {
        "production_units": (0, 5_000),
    },
    "costs_clean": {
        "water_cost_inr":     (0, None),
        "energy_cost_inr":    (0, None),
        "treatment_cost_inr": (0, None),
        "total_cost_inr":     (0, None),
    },
}

RESULTS: list[dict] = []


# -- Logging helper ------------------------------------------------------------
def record(dataset: str, check: str, column: str, records: int, status: str, detail: str = ""):
    RESULTS.append({
        "dataset":          dataset,
        "check":            check,
        "column":           column,
        "records_affected": records,
        "status":           status,
        "detail":           detail,
        "timestamp":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    icon = "✅" if status == "PASSED" else ("[WARN]️ " if status == "WARNING" else "[ERROR]")
    print(f"  {icon} [{dataset}] {check} | {column} | {records} records | {status}")
    if detail:
        print(f"       -> {detail}")


# -----------------------------------------------------------------------------
# Check 1: Completeness
# -----------------------------------------------------------------------------
def check_completeness(df: pd.DataFrame, name: str, key_cols: list[str]):
    for col in df.columns:
        n_null = df[col].isnull().sum()
        if col in key_cols:
            status = "FAILED" if n_null > 0 else "PASSED"
        else:
            status = "WARNING" if n_null > 0 else "PASSED"
        record(name, "Completeness", col, n_null, status,
               f"{n_null} null values in '{col}'" if n_null else "")


# -----------------------------------------------------------------------------
# Check 2: Uniqueness
# -----------------------------------------------------------------------------
def check_uniqueness(df: pd.DataFrame, name: str, key_cols: list[str]):
    n_dup = df.duplicated(subset=key_cols).sum()
    status = "PASSED" if n_dup == 0 else "WARNING"
    record(name, "Uniqueness", str(key_cols), n_dup, status,
           f"{n_dup} duplicate rows on {key_cols}" if n_dup else "")


# -----------------------------------------------------------------------------
# Check 3: Range
# -----------------------------------------------------------------------------
def check_ranges(df: pd.DataFrame, name: str):
    if name not in RANGES:
        return
    for col, (low, high) in RANGES[name].items():
        if col not in df.columns:
            continue
        mask = pd.Series([False] * len(df))
        if low is not None:
            mask = mask | (df[col] < low)
        if high is not None:
            mask = mask | (df[col] > high)
        n_violation = mask.sum()
        status = "PASSED" if n_violation == 0 else "WARNING"
        bound_str = f"[{low}, {high}]" if high else f"[{low}, ∞)"
        record(name, "Range check", col, n_violation, status,
               f"{n_violation} values outside {bound_str}" if n_violation else "")


# -----------------------------------------------------------------------------
# Check 4: Referential Integrity
# -----------------------------------------------------------------------------
def check_referential(df: pd.DataFrame, name: str, dim_plant: pd.DataFrame):
    if "plant_id" not in df.columns:
        return
    valid_ids = set(dim_plant["plant_id"])
    orphan = (~df["plant_id"].isin(valid_ids)).sum()
    status = "PASSED" if orphan == 0 else "FAILED"
    record(name, "Referential integrity", "plant_id", orphan, status,
           f"{orphan} rows with plant_id not in dim_plant" if orphan else "")


# -----------------------------------------------------------------------------
# Check 5: Consistency
# -----------------------------------------------------------------------------
def check_consistency_water(df: pd.DataFrame):
    name = "water_usage_clean"

    # recycling % must equal recycled/consumption * 100
    calc = (df["recycled_water_liters"] / df["water_consumption_liters"] * 100).round(2)
    mismatch = (abs(calc - df["recycling_percentage"]) > 0.5).sum()
    record(name, "Consistency", "recycling_percentage", mismatch,
           "PASSED" if mismatch == 0 else "WARNING",
           f"{mismatch} rows where recycling_pct deviates from formula" if mismatch else "")

    # net_water >= 0
    neg_net = (df["net_water_liters"] < 0).sum()
    record(name, "Consistency", "net_water_liters", neg_net,
           "PASSED" if neg_net == 0 else "WARNING",
           f"{neg_net} rows where net_water < 0" if neg_net else "")

    # recycled <= consumption
    invalid_recycled = (df["recycled_water_liters"] > df["water_consumption_liters"]).sum()
    record(name, "Consistency", "recycled > consumption", invalid_recycled,
           "PASSED" if invalid_recycled == 0 else "FAILED",
           f"{invalid_recycled} rows where recycled > consumed" if invalid_recycled else "")


def check_consistency_costs(df: pd.DataFrame):
    name = "costs_clean"
    calc_total = df["water_cost_inr"] + df["energy_cost_inr"] + df["treatment_cost_inr"]
    mismatch = (abs(calc_total - df["total_cost_inr"]) > 1.0).sum()
    record(name, "Consistency", "total_cost_inr", mismatch,
           "PASSED" if mismatch == 0 else "WARNING",
           f"{mismatch} rows where total_cost ≠ sum of components" if mismatch else "")


# -----------------------------------------------------------------------------
# Check 6: Quality Status Distribution
# -----------------------------------------------------------------------------
def check_quality_distribution(df: pd.DataFrame):
    dist = df["quality_status"].value_counts()
    total = len(df)
    for status_val, count in dist.items():
        pct = count / total * 100
        severity = "WARNING" if status_val in ["Warning", "Critical"] else "PASSED"
        record("water_quality_clean", "Quality distribution", status_val,
               count, severity, f"{count} rows ({pct:.1f}%)")


# -----------------------------------------------------------------------------
# Summary printer
# -----------------------------------------------------------------------------
def print_summary():
    df = pd.DataFrame(RESULTS)
    passed  = (df["status"] == "PASSED").sum()
    warning = (df["status"] == "WARNING").sum()
    failed  = (df["status"] == "FAILED").sum()

    print("\n" + "=" * 60)
    print("  DATA QUALITY REPORT SUMMARY")
    print("=" * 60)
    print(f"  ✅ Passed  : {passed}")
    print(f"  [WARN]️  Warnings: {warning}")
    print(f"  [ERROR] Failed  : {failed}")
    print(f"  Total checks: {len(df)}")
    print("=" * 60)

    if failed > 0:
        print("\n  [ERROR] FAILED CHECKS:")
        for _, row in df[df["status"] == "FAILED"].iterrows():
            print(f"     [{row['dataset']}] {row['check']} -> {row['detail']}")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("  PHASE 4 — Data Quality Validation")
    print("=" * 60)

    # Load cleaned datasets
    plants     = pd.read_csv(PROC_DIR / "plants_clean.csv")
    water      = pd.read_csv(PROC_DIR / "water_usage_clean.csv")
    quality    = pd.read_csv(PROC_DIR / "water_quality_clean.csv")
    energy     = pd.read_csv(PROC_DIR / "energy_usage_clean.csv")
    production = pd.read_csv(PROC_DIR / "production_clean.csv")
    costs      = pd.read_csv(PROC_DIR / "costs_clean.csv")

    datasets = {
        "plants_clean":        (plants,     ["plant_id"]),
        "water_usage_clean":   (water,      ["date", "plant_id"]),
        "water_quality_clean": (quality,    ["date", "plant_id"]),
        "energy_usage_clean":  (energy,     ["date", "plant_id"]),
        "production_clean":    (production, ["date", "plant_id"]),
        "costs_clean":         (costs,      ["date", "plant_id"]),
    }

    print("\n  Running completeness checks...")
    for name, (df, keys) in datasets.items():
        check_completeness(df, name, keys)

    print("\n  Running uniqueness checks...")
    for name, (df, keys) in datasets.items():
        check_uniqueness(df, name, keys)

    print("\n  Running range checks...")
    for name, (df, _) in datasets.items():
        check_ranges(df, name)

    print("\n  Running referential integrity checks...")
    for name, (df, _) in datasets.items():
        check_referential(df, name, plants)

    print("\n  Running consistency checks...")
    check_consistency_water(water)
    check_consistency_costs(costs)

    print("\n  Running quality status distribution check...")
    check_quality_distribution(quality)

    # Save report
    report_df = pd.DataFrame(RESULTS)
    report_path = REPORTS_DIR / "data_quality_report.csv"
    report_df.to_csv(report_path, index=False)
    print(f"\n  📄 Data quality report saved -> {report_path}")

    print_summary()
    return report_df


if __name__ == "__main__":
    main()
