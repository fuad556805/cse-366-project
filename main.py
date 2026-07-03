"""
main.py

Kaj: NL -> SQL pipeline interactive mode.
Ekbar run korlei bar bar proshno kora jabe.

Bug fixes:
- Model ek-bar-i load kora hoy (protyek query-te abar load kora hoto, fixed)
- schema["Gender"] hardcode crash fix kora hoise
- run_pipeline e model/vectorizer parameter hisebe pass kora hoy ekhon
"""

import sys
import os

# "core" folder-ke Python path-e add kora jate shob module import hoy
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "core"))

from dataset_loader import load_dataset
from schema_reader import read_schema
from intent_detector import load_model, predict_intent
from sql_generator import build_query, query_to_sql
from sql_validator import validate_sql
from sql_executor import execute_query
from response import print_result


def run_pipeline(df, schema, question, model, vectorizer,
                 db_path="data/database.db", table_name="data"):
    """
    Pura pipeline chalao — df, schema, question, model, vectorizer diye.
    Model ekhane load kora hoy na, main() theke pass kora hoy.
    """

    # Step 1: Intent detect
    intent = predict_intent(question, model, vectorizer)

    # Step 2: Internal query banano
    query = build_query(question, schema, intent)

    # Step 3: SQL string generate
    sql = query_to_sql(query, table_name)

    # Debug info
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

    # CSV + schema ekbar load koro
    csv_path = input("CSV file path din (default: data/sample.csv): ").strip()
    if not csv_path:
        csv_path = "data/sample.csv"

    db_path = "data/database.db"
    table_name = "data"

    try:
        df = load_dataset(csv_path, db_path, table_name)
    except FileNotFoundError as e:
        print("Error:", e)
        return

    schema = read_schema(df)

    # Model + vectorizer shudhu ek-bar load kora hoy — protyek query-te
    # abar load kora dorkar nei, tai main()-e rakha hoise.
    try:
        model, vectorizer = load_model("models/intent_model.pkl",
                                       "models/vectorizer.pkl")
    except FileNotFoundError:
        print("Error: Model file paoa jay nai. Prothome train koran:")
        print("  python3 models/train_intent.py")
        return

    print("\nEkhon joto khushi proshno korte paren.")
    print("'exit' likhe ber hoye jaben.")
    print("'change_csv' likhe notun CSV file load korte parben.\n")

    while True:
        try:
            question = input("Apnar proshno: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye bye!")
            break

        if not question:
            continue

        if question.lower() in ("exit", "quit", "q"):
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
        run_pipeline(df, schema, question, model, vectorizer, db_path, table_name)
        print("\n" + "-" * 50 + "\n")


if __name__ == "__main__":
    main()
