"""
dataset_loader.py

Kaj: CSV file load kore pandas DataFrame banay,
ebong sei DataFrame ke SQLite database e save kore.
"""

import os
import sqlite3
import pandas as pd


def load_csv(csv_path):
    """CSV file poira DataFrame return kore."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError("File paoa jay nai: " + csv_path)

    df = pd.read_csv(csv_path)
    return df


def save_to_sqlite(df, db_path, table_name="data"):
    """DataFrame ke SQLite database file e save kore."""
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
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
