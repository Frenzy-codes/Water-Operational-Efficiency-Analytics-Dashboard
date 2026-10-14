"""
run_sql_analysis.py
-----------------------------------------------------------------------------
Executes all 12 analytical SQL queries from sql/analysis.sql against MySQL
and exports the formatted results into reports/sql_query_results.md
-----------------------------------------------------------------------------
"""

import sys
import io
# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
SQL_PATH = BASE_DIR / "sql" / "analysis.sql"
REPORT_PATH = BASE_DIR / "reports" / "sql_query_results.md"

def get_engine():
    load_dotenv(BASE_DIR / ".env")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    db   = os.getenv("DB_NAME", "ecolab_analytics")
    user = os.getenv("DB_USER", "root")
    pwd  = os.getenv("DB_PASSWORD", "root")
    return create_engine(f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}")

def main():
    engine = get_engine()
    with open(SQL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into sections based on QUERY marker
    import re
    queries = re.split(r"-- =+\n-- (QUERY \d+:[^\n]+)\n-- ([^\n]+)\n-- =+", content)

    markdown_lines = [
        "# SQL Analytical Query Results",
        "",
        "> Database: `ecolab_analytics` | Execution Date: 2026-10-07",
        "",
        "This document contains the live execution results for all 12 analytical business intelligence queries.",
        ""
    ]

    # queries[0] is preamble (USE ecolab_analytics;)
    # then triplets: title, question, query_text
    i = 1
    query_num = 1
    while i < len(queries):
        title = queries[i].strip()
        question = queries[i+1].strip()
        sql_body = queries[i+2].strip()
        # Clean trailing comments or next query preamble
        clean_sql = sql_body.split(";")[0].strip()

        print(f"Executing {title}...")
        try:
            with engine.connect() as conn:
                df = pd.read_sql(clean_sql, conn)
            
            markdown_lines.append(f"## {title}")
            markdown_lines.append(f"> **{question}**")
            markdown_lines.append("")
            markdown_lines.append("```sql")
            markdown_lines.append(clean_sql + ";")
            markdown_lines.append("```")
            markdown_lines.append("")
            markdown_lines.append("### Results:")
            markdown_lines.append(df.to_markdown(index=False))
            markdown_lines.append("")
            markdown_lines.append("---")
            markdown_lines.append("")
        except Exception as e:
            print(f"Error on {title}: {e}")

        i += 3
        query_num += 1

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_lines))

    print(f"\n[DONE] Saved SQL results to {REPORT_PATH}")

if __name__ == "__main__":
    main()
