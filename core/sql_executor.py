"""
sql_executor.py

Kaj: generated SQL query database e run kore result ber kora.

Backend:
- DATABASE_URL / NEON_DATABASE_URL env var thakle -> PostgreSQL (Neon DB)
- Na thakle -> SQLite (local dev fallback)
"""

import os
import sqlite3


def _get_database_url():
    """Neon DB URL return kore, na thakle None."""
    url = os.environ.get("DATABASE_URL") or os.environ.get("NEON_DATABASE_URL")
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def _execute_postgres(sql, database_url):
    """
    PostgreSQL (Neon DB) te SQL run kore.
    psycopg2 use kore.
    """
    import psycopg2

    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        if cursor.description:
            column_names = [desc[0] for desc in cursor.description]
        else:
            column_names = []
    finally:
        cursor.close()
        conn.close()

    return column_names, rows


def _execute_sqlite(sql, db_path):
    """SQLite e SQL run kore (local dev)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        if cursor.description:
            column_names = [desc[0] for desc in cursor.description]
        else:
            column_names = []
    finally:
        conn.close()

    return column_names, rows


def execute_query(sql, db_path="data/database.db"):
    """
    SQL query run kore.

    Return:
        column_names (list): result column name gula
        rows (list of tuples): result row gula

    SQL bhul thakle exception raise korbe (caller handle korbe).
    """
    database_url = _get_database_url()
    if database_url:
        return _execute_postgres(sql, database_url)
    else:
        return _execute_sqlite(sql, db_path)


# Quick test
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from dataset_loader import load_dataset

    load_dataset("../data/sample.csv", "../data/database.db")

    cols, rows = execute_query(
        'SELECT * FROM "data" LIMIT 3', "../data/database.db"
    )
    print("Columns:", cols)
    for r in rows:
        print(r)
