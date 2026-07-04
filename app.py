"""
app.py

Kaj: Flask web server — NL to SQL AI-er frontend serve kore.
     Core pipeline logic e kono changes nei, sudhu web layer.

Deployment:
- Render + Neon DB: DATABASE_URL env var set thakle PostgreSQL use hoy
- Local dev: SQLite fallback (data/database.db)
"""

import os
import sys
import uuid
import tempfile

from flask import Flask, request, jsonify, render_template

# core folder path add
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "core"))

from dataset_loader import load_dataset
from schema_reader import read_schema
from intent_detector import load_model, predict_intent
from sql_generator import build_query, query_to_sql
from sql_validator import validate_sql
from sql_executor import execute_query

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB upload cap
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-change-in-prod")

# Production e PostgreSQL, local dev e SQLite
USE_POSTGRES = bool(
    os.environ.get("DATABASE_URL") or os.environ.get("NEON_DATABASE_URL")
)

# SQLite path (local dev only)
DB_PATH = "data/database.db"
TABLE_NAME = "data"

if not USE_POSTGRES:
    os.makedirs("data", exist_ok=True)

# ── Global state (single-user; multi-user hobe Task #4 e) ─────────────────
_state = {
    "df":         None,
    "schema":     None,
    "model":      None,
    "vectorizer": None,
}

# Model load at startup
try:
    _state["model"], _state["vectorizer"] = load_model(
        "models/intent_model.pkl", "models/vectorizer.pkl"
    )
except FileNotFoundError:
    print("WARNING: Model files not found. Run: python3 models/train_intent.py")


# ── Routes ────────────────────────────────────────────────────────────────

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

    # Temporary file use koro — Render-er ephemeral disk-e safe
    tmp = tempfile.NamedTemporaryFile(
        suffix=".csv", delete=False, prefix="nl2sql_"
    )
    try:
        f.save(tmp.name)
        tmp.close()

        try:
            df = load_dataset(tmp.name, DB_PATH, TABLE_NAME)
            schema = read_schema(df)
        except Exception as e:
            print(f"Upload error: {e}")
            return jsonify({
                "error": "Failed to parse CSV. Ensure the file is valid with a header row."
            }), 500
    finally:
        # Temp file sokol kshetrey delete koro
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    _state["df"] = df
    _state["schema"] = schema

    preview_cols = list(df.columns)
    preview_rows = df.head(5).fillna("").values.tolist()

    return jsonify({
        "success":  True,
        "filename": f.filename,
        "rows":     len(df),
        "columns":  preview_cols,
        "preview":  preview_rows,
        "backend":  "postgresql" if USE_POSTGRES else "sqlite",
    })


@app.route("/ask", methods=["POST"])
def ask():
    """Natural language question niye SQL generate kore execute kore result pathay."""
    if _state["df"] is None:
        return jsonify({"error": "No dataset loaded. Please upload a CSV first."}), 400

    if _state["model"] is None:
        return jsonify({"error": "Model not loaded. Run: python3 models/train_intent.py"}), 500

    data     = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Question is empty"}), 400

    df         = _state["df"]
    schema     = _state["schema"]
    model      = _state["model"]
    vectorizer = _state["vectorizer"]

    # ── NL2SQL Pipeline ───────────────────────────────────────────────────
    intent = predict_intent(question, model, vectorizer)
    query  = build_query(question, schema, intent)
    try:
        sql = query_to_sql(query, TABLE_NAME)
    except ValueError as e:
        # Column bhul kore guess na kore, clear error dekhano hoy
        return jsonify({
            "sql":     None,
            "intent":  intent,
            "error":   str(e),
            "columns": [],
            "rows":    [],
        })

    is_valid, validation_msg = validate_sql(sql, schema, TABLE_NAME)
    if not is_valid:
        return jsonify({
            "sql":     sql,
            "intent":  intent,
            "error":   f"SQL validation failed: {validation_msg}",
            "columns": [],
            "rows":    [],
        })

    try:
        columns, rows = execute_query(sql, DB_PATH)
    except Exception as e:
        print(f"Query execution error: {e}")
        return jsonify({
            "sql":     sql,
            "intent":  intent,
            "error":   "Query execution failed. The generated SQL could not be run.",
            "columns": [],
            "rows":    [],
        })

    return jsonify({
        "sql":     sql,
        "intent":  intent,
        "error":   None,
        "columns": columns,
        "rows":    [list(r) for r in rows],
        "count":   len(rows),
    })


@app.route("/health")
def health():
    """Render health check endpoint."""
    return jsonify({
        "status":  "ok",
        "model":   _state["model"] is not None,
        "backend": "postgresql" if USE_POSTGRES else "sqlite",
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
