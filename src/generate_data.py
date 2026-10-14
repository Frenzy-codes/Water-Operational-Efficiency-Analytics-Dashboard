"""
generate_data.py
-----------------------------------------------------------------------------
Water & Operational Efficiency Analytics Dashboard
Phase 2: Synthetic Dataset Generation

Generates 12 months of realistic daily data (2026-01-01 -> 2026-12-31)
for 8 industrial plants. Intentionally introduces:
  - Seasonal patterns (higher summer water usage)
  - ~5% abnormal quality readings for meaningful analysis
  - Plant P004 as a persistent "problem plant" (high consumption, poor quality)
  - Occasional missing values & duplicates for the ETL to clean
-----------------------------------------------------------------------------
"""

import sys
import io
# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import numpy as np
import pandas as pd
from pathlib import Path

# -- Reproducibility --------------------------------------------------------
np.random.seed(42)

# -- Output directory --------------------------------------------------------
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# -- Plant master data --------------------------------------------------------
PLANTS = [
    {"plant_id": "P001", "plant_name": "Pune Central",      "location": "Pune",      "plant_type": "Treatment",     "capacity_liters": 100000},
    {"plant_id": "P002", "plant_name": "Mumbai West",        "location": "Mumbai",    "plant_type": "Manufacturing", "capacity_liters": 120000},
    {"plant_id": "P003", "plant_name": "Nashik North",       "location": "Nashik",    "plant_type": "Treatment",     "capacity_liters": 90000},
    {"plant_id": "P004", "plant_name": "Aurangabad East",    "location": "Aurangabad","plant_type": "Treatment",     "capacity_liters": 110000},  # problem plant
    {"plant_id": "P005", "plant_name": "Solapur South",      "location": "Solapur",   "plant_type": "Manufacturing", "capacity_liters": 95000},
    {"plant_id": "P006", "plant_name": "Nagpur Industrial",  "location": "Nagpur",    "plant_type": "Industrial",    "capacity_liters": 130000},
    {"plant_id": "P007", "plant_name": "Kolhapur West",      "location": "Kolhapur",  "plant_type": "Treatment",     "capacity_liters": 85000},
    {"plant_id": "P008", "plant_name": "Amravati Central",   "location": "Amravati",  "plant_type": "Industrial",    "capacity_liters": 105000},
]

PLANT_IDS = [p["plant_id"] for p in PLANTS]
DATE_RANGE = pd.date_range(start="2026-01-01", end="2026-12-31", freq="D")


# -- Helper: seasonal multiplier ---------------------------------------------
def seasonal_factor(month: int) -> float:
    """Peak consumption in May–June (Indian summer), lower in winter."""
    factors = {1: 0.85, 2: 0.88, 3: 0.95, 4: 1.05,
                5: 1.20, 6: 1.18, 7: 1.05, 8: 1.00,
                9: 0.95, 10: 0.90, 11: 0.88, 12: 0.83}
    return factors[month]


# -----------------------------------------------------------------------------
# 1. plants.csv
# -----------------------------------------------------------------------------
def generate_plants() -> pd.DataFrame:
    df = pd.DataFrame(PLANTS)
    df.to_csv(RAW_DIR / "plants.csv", index=False)
    print(f"  [OK] plants.csv          -> {len(df)} rows")
    return df


# -----------------------------------------------------------------------------
# 2. water_usage.csv
# -----------------------------------------------------------------------------
def generate_water_usage() -> pd.DataFrame:
    rows = []
    for date in DATE_RANGE:
        sf = seasonal_factor(date.month)
        for plant_id in PLANT_IDS:
            # P004 consumes ~30% more than average (problem plant)
            base = 70000 if plant_id == "P004" else 55000
            water = int(np.random.normal(base * sf, base * 0.08))
            water = max(20000, water)  # floor

            recycled = int(water * np.random.uniform(0.20, 0.45))
            rows.append({
                "date":                      date.date(),
                "plant_id":                  plant_id,
                "water_consumption_liters":  water,
                "recycled_water_liters":     recycled,
            })

    df = pd.DataFrame(rows)

    # Introduce ~20 deliberate duplicates
    dup_idx = np.random.choice(df.index, size=20, replace=False)
    df = pd.concat([df, df.loc[dup_idx]], ignore_index=True)

    # Introduce ~15 missing values in water_consumption_liters
    missing_idx = np.random.choice(df.index, size=15, replace=False)
    df.loc[missing_idx, "water_consumption_liters"] = np.nan

    df.to_csv(RAW_DIR / "water_usage.csv", index=False)
    print(f"  [OK] water_usage.csv     -> {len(df)} rows (incl. dupes & nulls)")
    return df


# -----------------------------------------------------------------------------
# 3. water_quality.csv
# -----------------------------------------------------------------------------
def generate_water_quality() -> pd.DataFrame:
    rows = []
    for date in DATE_RANGE:
        for plant_id in PLANT_IDS:
            # Determine if this reading is anomalous
            is_problem_plant = plant_id == "P004"
            is_anomaly = is_problem_plant or (np.random.random() < 0.05)
            # Monsoon months (Jul–Sep) have elevated turbidity
            is_monsoon = date.month in [7, 8, 9]

            if is_anomaly:
                ph        = round(np.random.uniform(4.5, 5.8), 2)
                turbidity = round(np.random.uniform(7.0, 15.0), 2)
                tds       = int(np.random.uniform(600, 1100))
                if ph < 5.5 or turbidity > 10 or tds > 1000:
                    status = "Critical"
                else:
                    status = "Warning"
            elif is_monsoon:
                ph        = round(np.random.uniform(6.3, 7.5), 2)
                turbidity = round(np.random.uniform(3.5, 6.5), 2)
                tds       = int(np.random.uniform(300, 520))
                status    = "Warning" if turbidity > 5 or tds > 500 else "Normal"
            else:
                ph        = round(np.random.uniform(6.5, 8.5), 2)
                turbidity = round(np.random.uniform(0.5, 4.5), 2)
                tds       = int(np.random.uniform(150, 490))
                status    = "Normal"

            rows.append({
                "date":          date.date(),
                "plant_id":      plant_id,
                "ph":            ph,
                "turbidity_ntu": turbidity,
                "tds_ppm":       tds,
                "quality_status": status,
            })

    df = pd.DataFrame(rows)
    df.to_csv(RAW_DIR / "water_quality.csv", index=False)
    print(f"  [OK] water_quality.csv   -> {len(df)} rows")
    return df


# -----------------------------------------------------------------------------
# 4. energy_usage.csv
# -----------------------------------------------------------------------------
def generate_energy_usage() -> pd.DataFrame:
    rows = []
    for date in DATE_RANGE:
        sf = seasonal_factor(date.month)
        for plant_id in PLANT_IDS:
            # Manufacturing plants use more energy
            base = 1800 if plant_id in ["P002", "P005"] else 1400
            # P006 Industrial — highest energy user
            if plant_id == "P006":
                base = 2200
            energy = round(np.random.normal(base * sf, base * 0.07), 1)
            energy = max(500, energy)
            rows.append({
                "date":       date.date(),
                "plant_id":   plant_id,
                "energy_kwh": energy,
            })

    df = pd.DataFrame(rows)
    # Introduce ~10 missing values
    missing_idx = np.random.choice(df.index, size=10, replace=False)
    df.loc[missing_idx, "energy_kwh"] = np.nan

    df.to_csv(RAW_DIR / "energy_usage.csv", index=False)
    print(f"  [OK] energy_usage.csv    -> {len(df)} rows (incl. nulls)")
    return df


# -----------------------------------------------------------------------------
# 5. production.csv
# -----------------------------------------------------------------------------
def generate_production() -> pd.DataFrame:
    rows = []
    for date in DATE_RANGE:
        for plant_id in PLANT_IDS:
            # Sundays have ~40% lower production
            is_sunday = date.dayofweek == 6
            base = 950 if plant_id in ["P002", "P006"] else 750
            units = int(np.random.normal(base * (0.6 if is_sunday else 1.0), base * 0.10))
            units = max(100, units)

            # Simulate occasional downtime (production = 0)
            if np.random.random() < 0.02:
                units = 0

            rows.append({
                "date":             date.date(),
                "plant_id":         plant_id,
                "production_units": units,
            })

    df = pd.DataFrame(rows)
    df.to_csv(RAW_DIR / "production.csv", index=False)
    print(f"  [OK] production.csv      -> {len(df)} rows")
    return df


# -----------------------------------------------------------------------------
# 6. costs.csv
# -----------------------------------------------------------------------------
def generate_costs(water_df: pd.DataFrame, energy_df: pd.DataFrame) -> pd.DataFrame:
    # Base rates (INR)
    WATER_RATE_PER_KL   = 18.5   # ₹ per 1000 liters
    ENERGY_RATE_PER_KWH = 7.2    # ₹ per kWh
    TREATMENT_RATE      = 0.035  # ₹ per liter treated

    # Use clean water_df for join (drop duplicates/nulls temporarily)
    w = water_df.dropna(subset=["water_consumption_liters"]).drop_duplicates(
        subset=["date", "plant_id"]
    )
    e = energy_df.dropna(subset=["energy_kwh"])

    merged = w.merge(e, on=["date", "plant_id"], how="inner")

    merged["water_cost_inr"] = (
        merged["water_consumption_liters"] / 1000 * WATER_RATE_PER_KL
    ).round(2)

    merged["energy_cost_inr"] = (
        merged["energy_kwh"] * ENERGY_RATE_PER_KWH
    ).round(2)

    merged["treatment_cost_inr"] = (
        merged["water_consumption_liters"] * TREATMENT_RATE
    ).round(2)

    # P004 has higher treatment cost (less efficient process)
    p004_mask = merged["plant_id"] == "P004"
    merged.loc[p004_mask, "treatment_cost_inr"] *= 1.35

    # Add small noise
    for col in ["water_cost_inr", "energy_cost_inr", "treatment_cost_inr"]:
        merged[col] = (merged[col] * np.random.uniform(0.97, 1.03, len(merged))).round(2)

    df = merged[["date", "plant_id", "water_cost_inr", "energy_cost_inr", "treatment_cost_inr"]].copy()
    df.to_csv(RAW_DIR / "costs.csv", index=False)
    print(f"  [OK] costs.csv           -> {len(df)} rows")
    return df


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("  PHASE 2 — Generating Synthetic Datasets")
    print("=" * 60)
    generate_plants()
    water_df  = generate_water_usage()
    generate_water_quality()
    energy_df = generate_energy_usage()
    generate_production()
    generate_costs(water_df, energy_df)
    print(f"\n  📁 Raw data saved to: {RAW_DIR}\n")


if __name__ == "__main__":
    main()
