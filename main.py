"""
main.py

Kaj: NL -> SQL pipeline interactive mode.
Ekbar run korlei bar bar proshno kora jabe.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "core"))

from dataset_loader import load_dataset
from schema_reader import read_schema
from intent_detector import load_model, predict_intent
from sql_generator import build_query, query_to_sql
from sql_validator import validate_sql
from sql_executor import execute_query
from response import print_result


def run_pipeline(df, schema, question, db_path="data/database.db", table_name="data"):
    """Pura pipeline chalao – df, schema, question diye."""
    # Step 1: Intent detect
    model, vectorizer = load_model("models/intent_model.pkl", "models/vectorizer.pkl")
    intent = predict_intent(question, model, vectorizer)

    # Step 2: Internal query banano
    query = build_query(question, schema, intent)

    # Step 3: SQL string generate
    sql = query_to_sql(query, table_name)

    print("Detected intent :", intent)
    print("Internal query  :", query)
    print("Generated SQL   :", sql)
    print()

    # Step 4: SQL validate
    is_valid, message = validate_sql(sql, schema, table_name)
    if not is_valid:
        print("SQL validation fail:", message)
        return

    # Step 5: SQL execute
    try:
        columns, rows = execute_query(sql, db_path)
    except Exception as e:
        print("SQL execute error:", e)
        return

    # Step 6: Result show
    print_result(columns, rows)


def main():
    print("=== NL to SQL AI (Interactive Mode) ===")

    # --- CSV + schema ekbar load koro (porer question e abar load kora lagbe na) ---
    csv_path = input("CSV file path din (default: data/sample.csv): ").strip()
    if not csv_path:
        csv_path = "data/sample.csv"

    db_path = "data/database.db"
    table_name = "data"
    df = load_dataset(csv_path, db_path, table_name)
    schema = read_schema(df)

    # Model + vectorizer ekbar load
    model, vectorizer = load_model("models/intent_model.pkl", "models/vectorizer.pkl")

    print("\nEkhon joto khushi proshno korte paren. 'exit' likhe ber hoye jaben.")
    print("'change_csv' likhe notun CSV file load korte parben.\n")

    while True:
        question = input("Apnar proshno: ").strip()

        if not question:
            continue

        if question.lower() in ["exit", "quit", "q"]:
            print("Bye bye!")
            break

        if question.lower() == "change_csv":
            new_csv = input("Notun CSV file path din: ").strip()
            if new_csv:
                try:
                    df = load_dataset(new_csv, db_path, table_name)
                    schema = read_schema(df)
                    print("CSV successfully changed.")
                except Exception as e:
                    print("CSV change error:", e)
            continue

        # Pipeline chalao
        run_pipeline(df, schema, question, db_path, table_name)
        print("\n" + "-" * 50 + "\n")
        print(schema["Gender"])


if __name__ == "__main__":
    main()