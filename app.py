"""
app.py

Kaj: Flask web server — NL to SQL AI-er frontend serve kore.
     Core pipeline logic e kono changes nei, sudhu web layer add kora hoise.
"""

import os
import sys
import uuid
import json

from flask import Flask, request, jsonify, render_template, send_from_directory

# core folder path add
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "core"))

from dataset_loader import load_dataset
from schema_reader import read_schema
from intent_detector import load_model, predict_intent
from sql_generator import build_query, query_to_sql
from sql_validator import validate_sql
from sql_executor import execute_query

app = Flask(__name__)

# Single-user local tool — global state is intentional (no concurrent users).
# For multi-user deployment, replace _state with per-session storage.
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB upload cap

UPLOAD_FOLDER = "data/uploads"
DB_PATH = "data/database.db"
TABLE_NAME = "data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global state (single-user CLI tool, so module-level is fine)
_state = {
    "df": None,
    "schema": None,
    "model": None,
    "vectorizer": None,
}

# Model ekbar load koro at startup
try:
    _state["model"], _state["vectorizer"] = load_model(
        "models/intent_model.pkl", "models/vectorizer.pkl"
    )
except FileNotFoundError:
    print("WARNING: Model files not found. Run python3 models/train_intent.py first.")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """CSV file upload kore schema return kore."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400

    if not f.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported"}), 400

    # Unique filename diye save koro
    safe_name = f"{uuid.uuid4().hex}.csv"
    save_path = os.path.join(UPLOAD_FOLDER, safe_name)
    f.save(save_path)

    try:
        df = load_dataset(save_path, DB_PATH, TABLE_NAME)
        schema = read_schema(df)
    except Exception:
        return jsonify({"error": "Failed to parse CSV. Ensure the file is valid and has a header row."}), 500

    _state["df"] = df
    _state["schema"] = schema

    # Preview: first 5 rows + columns
    preview_cols = list(df.columns)
    preview_rows = df.head(5).fillna("").values.tolist()

    return jsonify({
        "success": True,
        "filename": f.filename,
        "rows": len(df),
        "columns": preview_cols,
        "preview": preview_rows,
    })


@app.route("/ask", methods=["POST"])
def ask():
    """Natural language question niye SQL generate kore execute kore result pathay."""
    if _state["df"] is None:
        return jsonify({"error": "No dataset loaded. Please upload a CSV first."}), 400

    if _state["model"] is None:
        return jsonify({"error": "Model not loaded. Run python3 models/train_intent.py"}), 500

    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Question is empty"}), 400

    df = _state["df"]
    schema = _state["schema"]
    model = _state["model"]
    vectorizer = _state["vectorizer"]

    # Pipeline
    intent = predict_intent(question, model, vectorizer)
    query = build_query(question, schema, intent)
    sql = query_to_sql(query, TABLE_NAME)

    is_valid, validation_msg = validate_sql(sql, schema, TABLE_NAME)
    if not is_valid:
        return jsonify({
            "sql": sql,
            "intent": intent,
            "error": f"SQL validation failed: {validation_msg}",
            "columns": [],
            "rows": [],
        })

    try:
        columns, rows = execute_query(sql, DB_PATH)
    except Exception:
        return jsonify({
            "sql": sql,
            "intent": intent,
            "error": "Query execution failed. The generated SQL could not be run against the dataset.",
            "columns": [],
            "rows": [],
        })

    # rows are tuples — convert to lists for JSON
    return jsonify({
        "sql": sql,
        "intent": intent,
        "error": None,
        "columns": columns,
        "rows": [list(r) for r in rows],
        "count": len(rows),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
