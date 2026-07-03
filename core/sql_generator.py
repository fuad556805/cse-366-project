"""
sql_generator.py

Kaj: intent + operator + attribute + value — shobkichu ekshathe kore
prothome ekta "internal query representation" (dictionary) banano,
tarpor sheta theke asol SQL query string toiri kora.

Internal query representation:
{
    "intent": "SELECT",
    "filters": [
        {"column": "Gender",   "operator": "=",       "value": "Female"},
        {"column": "Age",      "operator": ">",        "value": "30"},
        {"column": "Score",    "operator": "BETWEEN",  "value": "5", "value2": "9"},
        {"column": "Notes",    "operator": "IS NULL"},
    ],
    "agg_column": None
}

Bug fixes (v2):
- Identifiers (column names, table name) ekhon double-quote diye quote
  kora hoy, jate multi-word column names ("First Name") valid SQL produce kore.
- Operator support align kora hoise: BETWEEN (2 number), IS NULL/IS NOT NULL
  (no value), LIKE (text value), simple binary ops — shob-i properly handled.
- build_query ekhon operator-centric: protyek detected operator-er upor
  iterate kore numbers / columns khoje, na number-centric.
- Duplicate function get_numeric_columns removed — schema_reader theke import.
- Filter deduplication: same column ekbar-er beshi filter-e thakbe na.
"""

import re

from operator_detector import detect_operators
from attribute_matcher import match_column, find_columns_in_text
from value_matcher import extract_numbers, match_categorical_values
from schema_reader import get_numeric_columns


# Aggregate intent gula
_AGGREGATE_INTENTS = {"AVG", "MAX", "MIN", "SUM"}

# Aggregate keyword -> SQL function mapping
_AGGREGATE_KEYWORDS = {
    "avg": "AVG", "average": "AVG", "mean": "AVG",
    "max": "MAX", "maximum": "MAX", "highest": "MAX",
    "largest": "MAX", "biggest": "MAX", "top": "MAX",
    "min": "MIN", "minimum": "MIN", "lowest": "MIN",
    "smallest": "MIN",
    "sum": "SUM", "total": "SUM",
}

# Operator category sets
_SIMPLE_OPS      = {">", "<", ">=", "<=", "=", "!=", "<>"}
_BETWEEN_OPS     = {"BETWEEN", "NOT BETWEEN"}
_NULL_OPS        = {"IS NULL", "IS NOT NULL"}
_LIKE_OPS        = {"LIKE"}
# IN/NOT IN needs a value list — too complex for current pipeline, skipped
_SKIP_OPS        = {"IN", "NOT IN"}


def _quote_identifier(name):
    """
    SQL identifier (column or table name) ke double-quote diye wrap kore.
    Already-quoted ba apostrophe-containing name-o handle hoy.
    Multi-word column name ("First Name") r jonno eta critical.
    """
    # Internal double-quote escape kora
    escaped = name.replace('"', '""')
    return f'"{escaped}"'


def _nearest_numeric_column(ref_pos, words_with_pos, schema,
                             synonyms_path="knowledge/synonyms.json"):
    """
    ref_pos character position theke shobcheye kache numeric column match kore.
    Return: column name (str) ba None.
    """
    numeric_columns = get_numeric_columns(schema)
    best_col = None
    best_dist = None
    for item in words_with_pos:
        col = match_column(item["word"], schema, synonyms_path)
        if col and col in numeric_columns:
            dist = abs(item["position"] - ref_pos)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_col = col
    return best_col


def _find_agg_column(question, schema,
                     synonyms_path="knowledge/synonyms.json"):
    """
    AVG/MAX/MIN/SUM intent-er jonno kon column-e function apply hobe seta ber kore.

    Strategy:
    - Question-e aggregate keyword (average, total, highest...) khonja.
    - Sei keyword-er shobcheye kache numeric column-matching word pick kora.
    - Match na pele prothom numeric column use kora.
    """
    numeric_columns = get_numeric_columns(schema)
    if not numeric_columns:
        return None

    question_lower = question.lower()
    words_with_pos = [
        {"word": m.group(), "position": m.start()}
        for m in re.finditer(r"\S+", question_lower)
    ]

    # Aggregate keyword-er position
    agg_keyword_pos = None
    for item in words_with_pos:
        if item["word"] in _AGGREGATE_KEYWORDS:
            agg_keyword_pos = item["position"]
            break

    best_col = None
    best_dist = None
    for item in words_with_pos:
        col = match_column(item["word"], schema, synonyms_path)
        if col and col in numeric_columns:
            dist = (abs(item["position"] - agg_keyword_pos)
                    if agg_keyword_pos is not None
                    else item["position"])
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_col = col

    return best_col if best_col else (numeric_columns[0] if numeric_columns else None)


def build_query(question, schema, intent,
                operators_path="knowledge/operators.json",
                synonyms_path="knowledge/synonyms.json"):
    """
    Question, schema ebong intent niye internal query representation banay.

    Return: {"intent": ..., "filters": [...], "agg_column": ...}
    """
    filters = []
    filtered_columns = set()   # duplicate column filter avoid

    # ── Step 1: Categorical filter (Gender='Female', District='Dhaka') ─────
    for match in match_categorical_values(question, schema):
        col = match["column"]
        if col not in filtered_columns:
            filters.append({"column": col, "operator": "=", "value": match["value"]})
            filtered_columns.add(col)

    # ── Step 2: Numeric / operator-based filter ────────────────────────────
    operators  = detect_operators(question, operators_path)
    all_numbers = extract_numbers(question)
    used_num_ids = set()      # track which number objects already used

    words_with_pos = [
        {"word": m.group(), "position": m.start()}
        for m in re.finditer(r"\S+", question.lower())
    ]

    for op in operators:
        symbol   = op["symbol"]
        op_pos   = op["position"]

        if symbol in _SKIP_OPS:
            continue

        # ── IS NULL / IS NOT NULL: no value needed ─────────────────
        if symbol in _NULL_OPS:
            col = _nearest_numeric_column(op_pos, words_with_pos, schema, synonyms_path)
            if not col:
                # Try text columns too for IS NULL
                for item in words_with_pos:
                    c = match_column(item["word"], schema, synonyms_path)
                    if c and c not in filtered_columns:
                        col = c
                        break
            if col and col not in filtered_columns:
                filters.append({"column": col, "operator": symbol})
                filtered_columns.add(col)
            continue

        # ── BETWEEN: needs two numbers after the operator ───────────
        if symbol in _BETWEEN_OPS:
            nums_after = sorted(
                [n for n in all_numbers
                 if n["position"] > op_pos and id(n) not in used_num_ids],
                key=lambda n: n["position"],
            )
            if len(nums_after) >= 2:
                col = _nearest_numeric_column(op_pos, words_with_pos, schema, synonyms_path)
                if col and col not in filtered_columns:
                    filters.append({
                        "column":  col,
                        "operator": symbol,
                        "value":   nums_after[0]["value"],
                        "value2":  nums_after[1]["value"],
                    })
                    filtered_columns.add(col)
                    used_num_ids.add(id(nums_after[0]))
                    used_num_ids.add(id(nums_after[1]))
            continue

        # ── LIKE: text-based matching (contains / starts with / ends with) ─
        if symbol in _LIKE_OPS:
            # LIKE-er jonno text-e quoted ba unquoted value tola complex —
            # simple approach: question theke operator-er pore prothom
            # non-number, non-stopword word newa
            col = _nearest_numeric_column(op_pos, words_with_pos, schema, synonyms_path)
            # LIKE usually text columns-e use hoy; skip numeric columns
            # value: operator-er pore prothom word
            words_after = [
                item for item in words_with_pos
                if item["position"] > op_pos
            ]
            if words_after:
                val = words_after[0]["word"]
                if not col:
                    # text column-er kach theke khoja
                    for item in words_with_pos:
                        c = match_column(item["word"], schema, synonyms_path)
                        if c and c not in filtered_columns:
                            col = c
                            break
                if col and col not in filtered_columns:
                    filters.append({
                        "column":   col,
                        "operator": "LIKE",
                        "value":    f"%{val}%",
                    })
                    filtered_columns.add(col)
            continue

        # ── Simple binary ops (>, <, >=, <=, =, !=) ────────────────
        if symbol in _SIMPLE_OPS:
            nums_after = sorted(
                [n for n in all_numbers
                 if n["position"] > op_pos and id(n) not in used_num_ids],
                key=lambda n: n["position"],
            )
            if not nums_after:
                continue
            nearest_num = nums_after[0]
            col = _nearest_numeric_column(nearest_num["position"],
                                          words_with_pos, schema, synonyms_path)
            if col and col not in filtered_columns:
                filters.append({
                    "column":   col,
                    "operator": symbol,
                    "value":    nearest_num["value"],
                })
                filtered_columns.add(col)
                used_num_ids.add(id(nearest_num))

    # ── Step 3: Build internal query ───────────────────────────────────────
    query = {
        "intent":     intent,
        "filters":    filters,
        "agg_column": None,
    }

    if intent in _AGGREGATE_INTENTS:
        query["agg_column"] = _find_agg_column(question, schema, synonyms_path)

    return query


def query_to_sql(query, table_name="data"):
    """
    Internal query representation theke asol SQL query string banay.

    Column name ebong table name shob double-quote diye wrap kora hoy,
    jate multi-word column names ("First Name") valid SQL produce kore.
    Supported filter types: simple binary, BETWEEN, IS NULL/IS NOT NULL, LIKE.
    """
    intent     = query["intent"]
    filters    = query["filters"]
    agg_column = query.get("agg_column")
    tbl        = _quote_identifier(table_name)

    # SELECT part
    if intent == "SELECT":
        select_part = "SELECT *"
    elif intent == "COUNT":
        select_part = "SELECT COUNT(*)"
    elif intent in _AGGREGATE_INTENTS:
        col = _quote_identifier(agg_column) if agg_column else "*"
        select_part = f"SELECT {intent}({col})"
    else:
        select_part = "SELECT *"

    sql = f"{select_part} FROM {tbl}"

    # WHERE clause
    if filters:
        conditions = []
        for f in filters:
            col_q    = _quote_identifier(f["column"])
            operator = f["operator"]

            if operator in _NULL_OPS:
                # IS NULL / IS NOT NULL — no value needed
                conditions.append(f"{col_q} {operator}")

            elif operator in _BETWEEN_OPS:
                v1 = f.get("value", "")
                v2 = f.get("value2", "")
                conditions.append(f"{col_q} {operator} {v1} AND {v2}")

            else:
                # Binary op (=, >, <, >=, <=, !=, LIKE)
                value     = str(f.get("value", ""))
                value_str = value
                # Numeric value hole quote lagbe na
                if value_str.replace(".", "", 1).lstrip("-").isdigit():
                    condition = f"{col_q} {operator} {value_str}"
                else:
                    safe = value_str.replace("'", "''")
                    condition = f"{col_q} {operator} '{safe}'"

                conditions.append(condition)

        sql += " WHERE " + " AND ".join(conditions)

    return sql


# Quick test
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    schema = {
        "Age":        {"dtype": "int64",   "sample_values": [30, 40]},
        "Gender":     {"dtype": "object",  "sample_values": ["Male", "Female"]},
        "District":   {"dtype": "object",  "sample_values": ["Dhaka", "Sylhet"]},
        "Score":      {"dtype": "float64", "sample_values": [8.5, 7.0]},
        "First Name": {"dtype": "object",  "sample_values": ["Rahim"]},
    }

    cases = [
        ("show female patients older than 30 from dhaka", "SELECT"),
        ("average age", "AVG"),
        ("highest score of female students", "MAX"),
        ("show age between 20 and 30", "SELECT"),
        ("show records where score is null", "SELECT"),
    ]

    for q, intent in cases:
        qr = build_query(q, schema, intent,
                         "../knowledge/operators.json",
                         "../knowledge/synonyms.json")
        print("Q     :", q)
        print("Query :", qr)
        print("SQL   :", query_to_sql(qr))
        print()
