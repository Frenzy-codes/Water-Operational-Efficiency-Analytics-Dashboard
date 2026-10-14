"""
run_pipeline.py
─────────────────────────────────────────────────────────────────────────────
Water & Operational Efficiency Analytics Dashboard
One-command End-to-End Automation Pipeline

Usage:
    python run_pipeline.py              # Full pipeline
    python run_pipeline.py --skip-sql  # Skip SQL load (no MySQL required)
    python run_pipeline.py --only-gen  # Only generate raw data

Pipeline stages:
    1. Generate synthetic datasets (data/raw/)
    2. Clean & transform data (data/processed/)
    3. Validate data quality (reports/)
    4. Load into MySQL database
─────────────────────────────────────────────────────────────────────────────
"""

import sys
import io
import time
import traceback
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add src/ to path
SRC_DIR = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_DIR))


def print_header(title: str):
    bar = "=" * 60
    print(f"\n{bar}")
    print(f"  {title}")
    print(f"{bar}")


def print_step(n: int, total: int, name: str):
    print(f"\n  +-- Step {n}/{total}: {name}")
    print(f"  |")


def print_step_done(elapsed: float):
    print(f"  |")
    print(f"  +-- [DONE] in {elapsed:.1f}s")


def run_stage(name: str, fn, step: int, total: int) -> bool:
    print_step(step, total, name)
    start = time.time()
    try:
        fn()
        print_step_done(time.time() - start)
        return True
    except Exception as e:
        print(f"  +-- [FAILED]: {e}")
        print(f"\n     Traceback:")
        traceback.print_exc()
        return False


def main():
    skip_sql = "--skip-sql" in sys.argv
    only_gen = "--only-gen" in sys.argv

    print_header("Water & Operational Efficiency Analytics - ETL Pipeline")
    print(f"  Started at : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if skip_sql:
        print("  Mode       : Skip SQL load")
    elif only_gen:
        print("  Mode       : Generate raw data only")
    else:
        print("  Mode       : Full pipeline")

    start_total = time.time()
    results = {}

    # ── Stage 1: Generate Data ──────────────────────────────────────────────
    import generate_data
    ok = run_stage("Generating synthetic datasets", generate_data.main, 1, 4)
    results["Data Generation"] = "[PASSED]" if ok else "[FAILED]"
    if not ok:
        print("\n  Pipeline aborted at Stage 1.")
        return

    if only_gen:
        print("\n  --only-gen flag set. Stopping after data generation.")
        _print_summary(results, start_total)
        return

    # ── Stage 2: ETL / Cleaning ─────────────────────────────────────────────
    import etl
    ok = run_stage("Cleaning & transforming data", etl.main, 2, 4)
    results["ETL / Cleaning"] = "[PASSED]" if ok else "[FAILED]"
    if not ok:
        print("\n  Pipeline aborted at Stage 2.")
        _print_summary(results, start_total)
        return

    # ── Stage 3: Validation ─────────────────────────────────────────────────
    import validation
    ok = run_stage("Running data quality validation", validation.main, 3, 4)
    results["Data Validation"] = "[PASSED]" if ok else "[FAILED]"

    # ── Stage 4: SQL Load ────────────────────────────────────────────────────
    if not skip_sql:
        import load_sql
        ok = run_stage("Loading data into MySQL", load_sql.main, 4, 4)
        results["MySQL Load"] = "[PASSED]" if ok else "[SKIPPED - check .env]"
    else:
        results["MySQL Load"] = "[SKIPPED - --skip-sql flag]"

    _print_summary(results, start_total)


def _print_summary(results: dict, start_total: float):
    elapsed = time.time() - start_total
    print_header("Pipeline Summary")
    for stage, status in results.items():
        print(f"  {status:<30} {stage}")
    print(f"\n  Total time: {elapsed:.1f}s")
    print(f"  Completed : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    all_passed = all("PASSED" in v or "SKIPPED" in v for v in results.values())
    if all_passed:
        print("  SUCCESS! Pipeline complete!")
        print("  Open Power BI Desktop to refresh your dashboard.")
        print("  -> Import CSVs from: data/processed/")
        print("  -> OR connect to MySQL: localhost / ecolab_analytics")
    else:
        print("  WARNING: Some stages failed. Check the output above for details.")
    print()


if __name__ == "__main__":
    main()
