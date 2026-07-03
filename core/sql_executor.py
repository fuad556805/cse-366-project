"""
sql_executor.py

Kaj: generated SQL query SQLite database e run kore result ber kora.

Improvement:
- cursor.description None check add kora hoise: kono result na hole
  (jemon COUNT(*) = 0) description kabhi kabhi None hote pare.
- Connection always close hoy — finally block maintain kora ache.
"""

import sqlite3


def execute_query(sql, db_path="data/database.db"):
    """
    SQL query run kore.

    Return:
        column_names (list): result column name gula
        rows (list of tuples): result row gula

    SQL bhul thakle exception raise korbe (caller handle korbe).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()

        # description None hole (e.g. result nai) empty column list
        if cursor.description:
            column_names = [desc[0] for desc in cursor.description]
        else:
            column_names = []
    finally:
        conn.close()

    return column_names, rows


# Quick test
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from dataset_loader import load_dataset

    load_dataset("../data/sample.csv", "../data/database.db")

    cols, rows = execute_query(
        "SELECT * FROM data LIMIT 3", "../data/database.db"
    )
    print("Columns:", cols)
    for r in rows:
        print(r)
