"""
dataset_loader.py

Kaj: CSV file load kore pandas DataFrame banay,
ebong sei DataFrame ke SQLite ba PostgreSQL database e save kore.

Backend:
- DATABASE_URL / NEON_DATABASE_URL env var set thakle -> PostgreSQL (Neon DB)
- Nahi thakle -> SQLite (local dev fallback)
"""

import os
import sqlite3
import pandas as pd


def load_csv(csv_path):
    """
    CSV file pore DataFrame return kore.
    Encoding: prothomey utf-8, na chole latin-1 try kore.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file paoa jay nai: {csv_path}")

    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="latin-1")

    return df


def _get_database_url():
    """
    Database connection URL return kore.
    DATABASE_URL (Render/Heroku standard) ba NEON_DATABASE_URL check kore.
    """
    return os.environ.get("DATABASE_URL") or os.environ.get("NEON_DATABASE_URL")


def save_to_postgres(df, table_name="data", database_url=None):
    """
    DataFrame ke PostgreSQL (Neon DB) te save kore.
    SQLAlchemy engine use kore pandas to_sql diye.
    """
    from sqlalchemy import create_engine, text

    # psycopg2 driver ensure koro
    url = database_url or _get_database_url()
    if not url:
        raise RuntimeError(
            "PostgreSQL URL paoa jay nai. "
            "DATABASE_URL ba NEON_DATABASE_URL environment variable set koro."
        )
    if url.startswith("postgres://"):
        # SQLAlchemy 1.4+ e "postgres://" depricated, "postgresql://" use koro
        url = url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(url, pool_pre_ping=True)

    # Table drop kore recreate koro (replace strategy)
    with engine.begin() as conn:
        conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))

    df.to_sql(table_name, engine, if_exists="replace", index=False)
    engine.dispose()


def save_to_sqlite(df, db_path, table_name="data"):
    """
    DataFrame ke SQLite database file e save kore.
    db_path-er directory automatically create hoy.
    """
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    finally:
        conn.close()

    return db_path


def load_dataset(csv_path, db_path="data/database.db", table_name="data"):
    """
    Main function: CSV load kore appropriate backend e save kore,
    ebong DataFrame ta return kore.

    Backend selection:
    - DATABASE_URL / NEON_DATABASE_URL set thakle: PostgreSQL (Neon)
    - Na thakle: SQLite (local dev)
    """
    df = load_csv(csv_path)

    database_url = _get_database_url()
    if database_url:
        save_to_postgres(df, table_name, database_url)
    else:
        save_to_sqlite(df, db_path, table_name)

    return df


# Quick test
if __name__ == "__main__":
    data = load_dataset("data/sample.csv", "data/database.db")
    print("Dataset load hoise. Total rows:", len(data))
    print(data.head())
