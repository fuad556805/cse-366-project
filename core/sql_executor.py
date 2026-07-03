"""
sql_executor.py

Kaj: generated SQL query SQLite database e run kore result ber kora.
"""

import sqlite3


def execute_query(sql, db_path="data/database.db"):
    """
    SQL query run kore. Return kore:
    - column_names: list of column name
    - rows: result rows

    SQL bhul thakle exception raise korbe (caller eta handle korbe).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
    finally:
        conn.close()

    return column_names, rows


# Quick test
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from dataset_loader import load_dataset

    load_dataset("../data/sample.csv", "../data/database.db")

    cols, rows = execute_query("SELECT * FROM data WHERE Gender = 'Female'", "../data/database.db")
    print(cols)
    for r in rows:
        print(r)
