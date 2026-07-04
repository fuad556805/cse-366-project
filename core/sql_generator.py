"""
sql_generator.py

Kaj: intent + operator + attribute + value — shobkichu ekshathe kore
prothome ekta "internal query representation" (dictionary) banano,
tarpor sheta theke asol SQL query string toiri kora.

Internal query representation:
{
    "intent":    "SELECT",
    "filters":   [
        {"column": "Gender",  "operator": "=",        "value": "Female"},
        {"column": "Age",     "operator": ">",         "value": "30"},
        {"column": "Score",   "operator": "BETWEEN",   "value": "5", "value2": "9"},
    ],
    "agg_column": None,        # AVG/MAX/MIN/SUM er jonno column
    "group_by":   None,        # "average salary by department" -> "Department"
    "order_by":   None,        # "top 10 salary" -> "Salary"
    "order_dir":  "DESC",      # "DESC" ba "ASC"
    "limit":      None,        # top N -> N
}

New features (v3):
- GROUP BY support: "average salary by department"
- ORDER BY + LIMIT: "top 10 highest salary", "lowest 5 prices"
- Underscore <-> space column matching (via improved attribute_matcher)
- Expanded synonym + operator dictionaries

v4 (bug fix — multi-word column jemon "Time Spent on Website (min)",
"Purchase Amount ($)" bhul kore "Customer ID"-r moto onno column select
kore felto):
- _find_agg_column(), _detect_order_limit(), _detect_group_by(),
  ebong filter matching — shobgulai ekhon match_column()-e SHUDHU EKTA
  word pathanor bodole find_columns_with_positions() use kore, jeta
  PURA multi-word column phrase ekshathe match kore.
- Bhul/dangerous fallback "numeric_columns[0]" shoriye deya hoise —
  column detect na hole ekhon None thake (bhul column-e query cholar
  bodole clear error deoya hoy, see query_to_sql).
"""

import re

from operator_detector import detect_operators
from attribute_matcher import find_columns_with_positions
from value_matcher import extract_numbers, match_categorical_values
from schema_reader import get_numeric_columns, get_text_columns


# ── Constants ────────────────────────────────────────────────────────────────

_AGGREGATE_INTENTS = {"AVG", "MAX", "MIN", "SUM"}

_AGGREGATE_KEYWORDS = {
    "avg": "AVG", "average": "AVG", "mean": "AVG",
    "max": "MAX", "maximum": "MAX", "highest": "MAX",
    "largest": "MAX", "biggest": "MAX", "top": "MAX",
    "min": "MIN", "minimum": "MIN", "lowest": "MIN",
    "smallest": "MIN",
    "sum": "SUM", "total": "SUM", "aggregate": "SUM",
}

_SIMPLE_OPS   = {">", "<", ">=", "<=", "=", "!=", "<>"}
_BETWEEN_OPS  = {"BETWEEN", "NOT BETWEEN"}
_NULL_OPS     = {"IS NULL", "IS NOT NULL"}
_LIKE_OPS     = {"LIKE"}
_SKIP_OPS     = {"IN", "NOT IN"}

# "top N" -> ORDER BY DESC LIMIT N
_TOP_PATTERN    = re.compile(r"\btop\s+(\d+)\b", re.IGNORECASE)
# "bottom/lowest/least N" -> ORDER BY ASC LIMIT N
_BOTTOM_PATTERN = re.compile(
    r"\b(?:bottom|lowest|least|worst|minimum)\s+(\d+)\b", re.IGNORECASE
)
# GROUP BY trigger: "by <column>" near end
_BY_PATTERN = re.compile(r"\bby\s+(.+)$", re.IGNORECASE)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _quote_identifier(name):
    """SQL identifier (column or table name) ke double-quote diye wrap kore."""
    escaped = name.replace('"', '""')
    return f'"{escaped}"'


def _nearest_column(ref_pos, column_matches, allowed=None, exclude=None):
    """
    ref_pos (character position)-er shobcheye kache-r matched column ta
    ber kore. allowed dile shudhu shei set-er modhye theke, exclude dile
    already-filtered column gula bad diye khoja hoy.
    """
    candidates = column_matches
    if allowed is not None:
        candidates = [c for c in candidates if c["column"] in allowed]
    if exclude:
        candidates = [c for c in candidates if c["column"] not in exclude]
    if not candidates:
        return None
    best = min(candidates, key=lambda c: (abs(c["position"] - ref_pos), -c["score"]))
    return best["column"]


def _find_agg_column(question, column_matches, numeric_columns):
    """
    AVG/MAX/MIN/SUM intent-er jonno kon column-e function apply hobe seta ber kore.
    Aggregate keyword-er shobcheye kache numeric column ta pick kora hoy
    (multi-word column phrase-o ekhon thik moto match hoy — dekho
    attribute_matcher.find_columns_with_positions()).

    Column detect na hole None return kore — kokhono bhul kore onno
    column (jemon "Customer ID") default hisebe select kora hoy na.
    """
    if not numeric_columns:
        return None

    agg_keyword_pos = None
    for m in re.finditer(r"\S+", question.lower()):
        if m.group() in _AGGREGATE_KEYWORDS:
            agg_keyword_pos = m.start()
            break

    numeric_matches = [c for c in column_matches if c["column"] in numeric_columns]
    if not numeric_matches:
        return None

    if agg_keyword_pos is None:
        best = max(numeric_matches, key=lambda c: c["score"])
        return best["column"]

    best = min(numeric_matches,
                key=lambda c: (abs(c["position"] - agg_keyword_pos), -c["score"]))
    return best["column"]


def _detect_group_by(question, column_matches):
    """
    "average salary by department" -> "Department" column ber kore.
    "count players by club"        -> "Club"
    Return: column name (str) ba None.
    """
    m = re.search(r"\bby\b", question, re.IGNORECASE)
    if not m:
        return None
    pos = m.end()
    candidates = [c for c in column_matches if c["position"] >= pos]
    if not candidates:
        return None
    best = min(candidates, key=lambda c: (c["position"], -c["score"]))
    return best["column"]


def _detect_order_limit(question, column_matches, numeric_columns):
    """
    "top 10 highest salary"  -> (order_col, "DESC", 10)
    "lowest 5 prices"        -> (order_col, "ASC",  5)
    Return: (column_name, direction, limit) or (None, None, None)

    Column bhul kore guess kora hoy na — na paile order_by None thake,
    (SQL-e LIMIT thakbe kintu ORDER BY thakbe na).
    """
    def _column_near(pos):
        candidates = [c for c in column_matches
                      if c["column"] in numeric_columns and c["position"] >= pos]
        if not candidates:
            candidates = [c for c in column_matches if c["column"] in numeric_columns]
        if not candidates:
            return None
        best = min(candidates, key=lambda c: (abs(c["position"] - pos), -c["score"]))
        return best["column"]

    top_m = _TOP_PATTERN.search(question)
    if top_m:
        n = int(top_m.group(1))
        col = _column_near(top_m.end())
        return col, "DESC", n

    bot_m = _BOTTOM_PATTERN.search(question)
    if bot_m:
        n = int(bot_m.group(1))
        col = _column_near(bot_m.end())
        return col, "ASC", n

    return None, None, None


# ── Main pipeline functions ───────────────────────────────────────────────────

def build_query(question, schema, intent,
                operators_path="knowledge/operators.json",
                synonyms_path="knowledge/synonyms.json"):
    """
    Question, schema ebong intent niye internal query representation banay.
    Return: {intent, filters, agg_column, group_by, order_by, order_dir, limit}
    """
    filters = []
    filtered_columns = set()

    numeric_columns = set(get_numeric_columns(schema))
    text_columns = set(get_text_columns(schema))

    # Pura question-e ekbar-e shob column-er match + position ber kore neya hoy
    # (multi-word phrase soho) — eta pure module e reuse hoy jate bar bar
    # single-word match_column() na call kore bhul column select na hoy.
    column_matches = find_columns_with_positions(question, schema, synonyms_path)

    # ── Step 1: Categorical filter ────────────────────────────────────────
    for match in match_categorical_values(question, schema):
        col = match["column"]
        if col not in filtered_columns:
            filters.append({"column": col, "operator": "=", "value": match["value"]})
            filtered_columns.add(col)

    # ── Step 2: Numeric / operator-based filter ───────────────────────────
    operators   = detect_operators(question, operators_path)
    all_numbers = extract_numbers(question)
    used_num_ids = set()

    for op in operators:
        symbol = op["symbol"]
        op_pos = op["position"]

        if symbol in _SKIP_OPS:
            continue

        # IS NULL / IS NOT NULL
        if symbol in _NULL_OPS:
            col = (_nearest_column(op_pos, column_matches,
                                    allowed=numeric_columns, exclude=filtered_columns)
                   or _nearest_column(op_pos, column_matches, exclude=filtered_columns))
            if col and col not in filtered_columns:
                filters.append({"column": col, "operator": symbol})
                filtered_columns.add(col)
            continue

        # BETWEEN
        if symbol in _BETWEEN_OPS:
            nums_after = sorted(
                [n for n in all_numbers
                 if n["position"] > op_pos and id(n) not in used_num_ids],
                key=lambda n: n["position"],
            )
            if len(nums_after) >= 2:
                col = _nearest_column(op_pos, column_matches,
                                       allowed=numeric_columns, exclude=filtered_columns)
                if col and col not in filtered_columns:
                    filters.append({
                        "column":   col,
                        "operator": symbol,
                        "value":    nums_after[0]["value"],
                        "value2":   nums_after[1]["value"],
                    })
                    filtered_columns.add(col)
                    used_num_ids.add(id(nums_after[0]))
                    used_num_ids.add(id(nums_after[1]))
            continue

        # LIKE
        if symbol in _LIKE_OPS:
            words_after = [
                m for m in re.finditer(r"\S+", question.lower())
                if m.start() > op_pos
            ]
            if words_after:
                val = words_after[0].group()
                col = (_nearest_column(op_pos, column_matches,
                                        allowed=text_columns, exclude=filtered_columns)
                       or _nearest_column(op_pos, column_matches, exclude=filtered_columns))
                if col and col not in filtered_columns:
                    filters.append({
                        "column":   col,
                        "operator": "LIKE",
                        "value":    f"%{val}%",
                    })
                    filtered_columns.add(col)
            continue

        # Simple binary ops (>, <, >=, <=, =, !=)
        if symbol in _SIMPLE_OPS:
            nums_after = sorted(
                [n for n in all_numbers
                 if n["position"] > op_pos and id(n) not in used_num_ids],
                key=lambda n: n["position"],
            )
            if not nums_after:
                continue
            nearest_num = nums_after[0]
            col = _nearest_column(nearest_num["position"], column_matches,
                                   allowed=numeric_columns, exclude=filtered_columns)
            if col and col not in filtered_columns:
                filters.append({
                    "column":   col,
                    "operator": symbol,
                    "value":    nearest_num["value"],
                })
                filtered_columns.add(col)
                used_num_ids.add(id(nearest_num))

    # ── Step 3: GROUP BY detection ────────────────────────────────────────
    group_by_col = _detect_group_by(question, column_matches)

    # ── Step 4: ORDER BY + LIMIT detection ───────────────────────────────
    order_col, order_dir, limit = _detect_order_limit(question, column_matches, numeric_columns)

    # ── Step 5: Aggregate column ──────────────────────────────────────────
    agg_col = None
    if intent in _AGGREGATE_INTENTS:
        agg_col = _find_agg_column(question, column_matches, numeric_columns)

    return {
        "intent":    intent,
        "filters":   filters,
        "agg_column": agg_col,
        "group_by":  group_by_col,
        "order_by":  order_col,
        "order_dir": order_dir or "DESC",
        "limit":     limit,
    }


def query_to_sql(query, table_name="data"):
    """
    Internal query representation theke asol SQL query string banay.
    GROUP BY, ORDER BY, LIMIT — shob support kora hoise.
    """
    intent     = query["intent"]
    filters    = query.get("filters", [])
    agg_column = query.get("agg_column")
    group_by   = query.get("group_by")
    order_by   = query.get("order_by")
    order_dir  = query.get("order_dir", "DESC")
    limit      = query.get("limit")
    tbl        = _quote_identifier(table_name)

    # ── SELECT clause ─────────────────────────────────────────────────────
    # Special case: LIMIT thakle kintu GROUP BY na thakle aggregate use kora thik
    # na (jemon "top 3 oldest" -> SELECT * ORDER BY ... LIMIT 3, MAX(...) na)
    agg_overridden_to_select = (
        limit is not None
        and group_by is None
        and intent in _AGGREGATE_INTENTS
    )

    if intent == "SELECT" or agg_overridden_to_select:
        select_part = "SELECT *"
    elif intent == "COUNT":
        if group_by:
            gb_col = _quote_identifier(group_by)
            select_part = f"SELECT {gb_col}, COUNT(*)"
        else:
            select_part = "SELECT COUNT(*)"
    elif intent in _AGGREGATE_INTENTS:
        if not agg_column:
            raise ValueError(
                "Kon column-e '" + intent + "' calculate korte hobe eta bujha jayni. "
                "Doya kore column-er naam ta ektu clear kore jiggesh koro "
                "(jemon 'average purchase amount' er bodole 'average of Purchase Amount column')."
            )
        col = _quote_identifier(agg_column)
        if group_by:
            gb_col = _quote_identifier(group_by)
            select_part = f"SELECT {gb_col}, {intent}({col})"
        else:
            select_part = f"SELECT {intent}({col})"
    else:
        select_part = "SELECT *"

    sql = f"{select_part} FROM {tbl}"

    # ── WHERE clause ──────────────────────────────────────────────────────
    if filters:
        conditions = []
        for f in filters:
            col_q    = _quote_identifier(f["column"])
            operator = f["operator"]

            if operator in _NULL_OPS:
                conditions.append(f"{col_q} {operator}")

            elif operator in _BETWEEN_OPS:
                v1 = f.get("value", "")
                v2 = f.get("value2", "")
                conditions.append(f"{col_q} {operator} {v1} AND {v2}")

            else:
                value = str(f.get("value", ""))
                if value.replace(".", "", 1).lstrip("-").isdigit():
                    conditions.append(f"{col_q} {operator} {value}")
                else:
                    safe = value.replace("'", "''")
                    conditions.append(f"{col_q} {operator} '{safe}'")

        sql += " WHERE " + " AND ".join(conditions)

    # ── GROUP BY clause ───────────────────────────────────────────────────
    if group_by:
        sql += f" GROUP BY {_quote_identifier(group_by)}"

    # ── ORDER BY + LIMIT clause ───────────────────────────────────────────
    if order_by:
        sql += f" ORDER BY {_quote_identifier(order_by)} {order_dir}"
    if limit:
        sql += f" LIMIT {limit}"

    return sql


# Quick test
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    schema = {
        "Name":       {"dtype": "object",  "sample_values": ["Alice"]},
        "Age":        {"dtype": "int64",   "sample_values": [30, 40]},
        "Gender":     {"dtype": "object",  "sample_values": ["Male", "Female"]},
        "Salary":     {"dtype": "float64", "sample_values": [50000, 80000]},
        "Department": {"dtype": "object",  "sample_values": ["CS", "EEE"]},
        "GPA":        {"dtype": "float64", "sample_values": [3.5, 3.8]},
        "District":   {"dtype": "object",  "sample_values": ["Dhaka", "Sylhet"]},
    }

    cases = [
        ("show female students older than 20", "SELECT"),
        ("average salary by department",       "AVG"),
        ("top 5 highest salary",               "SELECT"),
        ("lowest 3 gpa",                       "SELECT"),
        ("count students by department",       "COUNT"),
        ("total salary of employees from dhaka", "SUM"),
        ("maximum gpa of female students",    "MAX"),
        ("how many employees",                 "COUNT"),
    ]

    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    op_path  = os.path.join(base, "knowledge", "operators.json")
    syn_path = os.path.join(base, "knowledge", "synonyms.json")

    for q, intent in cases:
        qr  = build_query(q, schema, intent, op_path, syn_path)
        sql = query_to_sql(qr)
        print(f"Q   : {q}")
        print(f"SQL : {sql}")
        print()
