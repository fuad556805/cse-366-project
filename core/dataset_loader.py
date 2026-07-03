"""
dataset_loader.py

Kaj: CSV file load kore pandas DataFrame banay,
ebong sei DataFrame ke SQLite database e save kore.

Improvement:
- load_csv: encoding fallback add kora hoise (utf-8 na chole
  latin-1 try kore), CSV encoding issue theke crash avoid kore.
- save_to_sqlite: os.makedirs diye db directory auto-create kore.
"""

import os
import sqlite3
import pandas as pd


def load_csv(csv_path):
    """
    CSV file pore DataFrame return kore.
    Encoding: prothomey utf-8, na chole latin-1 (ISO-8859-1) try kore.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file paoa jay nai: {csv_path}")

    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="latin-1")

    return df


def save_to_sqlite(df, db_path, table_name="data"):
    """
    DataFrame ke SQLite database file e save kore.
    db_path-er directory automatically create hoy jodi na thake.
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
    Main function: CSV load kore, SQLite e save kore,
    ebong DataFrame ta return kore jate porer step gula
    (schema reading, query execution) eta use korte pare.
    """
    df = load_csv(csv_path)
    save_to_sqlite(df, db_path, table_name)
    return df


# Quick test (file ta directly run korle eta cholbe)
if __name__ == "__main__":
    data = load_dataset("data/sample.csv", "data/database.db")
    print("Dataset load hoise. Total rows:", len(data))
    print(data.head())
