"""
sql_generator.py

Kaj: intent + operator + attribute + value - shobkichu ekshathe kore
prothome ekta "internal query representation" (dictionary/JSON) banano,
tarpor sheta theke asol SQL query string toiri kora.

Internal query representation dekhte emon hoy:
{
    "intent": "SELECT",
    "filters": [
        {"column": "Gender", "operator": "=", "value": "Female"},
        {"column": "Age", "operator": ">", "value": "30"}
    ],
    "agg_column": None
}
"""

import re

from operator_detector import detect_operators
from attribute_matcher import match_column
from value_matcher import extract_numbers, match_categorical_values


def get_numeric_columns(schema):
    """Schema theke shudhu numeric (int/float) column gula ber kore."""
    numeric_columns = []
    for column, info in schema.items():
        if "int" in info["dtype"] or "float" in info["dtype"]:
            numeric_columns.append(column)
    return numeric_columns


def build_query(question, schema, intent):
    """
    Question, schema ebong (intent_detector theke paoa) intent niye
    internal query representation banay.
    """
    filters = []

    # Step 1: categorical filter (jemon Gender='Female', District='Dhaka')
    categorical_matches = match_categorical_values(question, schema)
    for match in categorical_matches:
        filters.append({
            "column": match["column"],
            "operator": "=",
            "value": match["value"]
        })

    # Step 2: numeric filter (jemon Age > 30)
    operators = detect_operators(question)
    numbers = extract_numbers(question)
    numeric_columns = get_numeric_columns(schema)

    # protyek word er shathe tar character position o rekhe dilam,
    # jate proti number-er "kache" (nearest) kon column-word ache
    # seta ber kora jay - erokom na korle duita numeric filter ekshathe
    # thakle (jemon "age>30 and marks>80") bhul column bosbe.
    words_with_position = [
        {"word": m.group(), "position": m.start()}
        for m in re.finditer(r"\S+", question.lower())
    ]

    for num in numbers:
        # ei number-er thik age shobcheye kache je operator ache seta neya
        nearest_operator = None
        for op in operators:
            if op["position"] < num["position"]:
                nearest_operator = op["symbol"]

        if nearest_operator is None:
            continue

        # ei number-er shobcheye kache (age ba pore, distance onujayi)
        # je numeric column-er naam paoa jay seta khoja
        matched_column = None
        best_distance = None
        for item in words_with_position:
            column = match_column(item["word"], schema)
            if column and column in numeric_columns:
                distance = abs(item["position"] - num["position"])
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    matched_column = column

        if matched_column:
            filters.append({
                "column": matched_column,
                "operator": nearest_operator,
                "value": num["value"]
            })

    query = {
        "intent": intent,
        "filters": filters,
        "agg_column": None
    }

    # Aggregate intent (AVG/MAX/MIN/SUM) hole kon column er upor
    # hishab hobe seta khuje ber kora dorkar.
    if intent in ("AVG", "MAX", "MIN", "SUM"):
        for item in words_with_position:
            column = match_column(item["word"], schema)
            if column and column in numeric_columns:
                query["agg_column"] = column
                break

    return query


def query_to_sql(query, table_name="data"):
    """Internal query representation theke asol SQL query string banay."""
    intent = query["intent"]
    filters = query["filters"]
    agg_column = query.get("agg_column")

    if intent == "SELECT":
        select_part = "SELECT *"
    elif intent == "COUNT":
        select_part = "SELECT COUNT(*)"
    elif intent in ("AVG", "MAX", "MIN", "SUM"):
        column = agg_column if agg_column else "*"
        select_part = "SELECT " + intent + "(" + column + ")"
    else:
        select_part = "SELECT *"

    sql = select_part + " FROM " + table_name

    if filters:
        conditions = []
        for f in filters:
            value = f["value"]
            # value ta number hole quote lagbe na, text hole quote lagbe
            if str(value).replace(".", "", 1).isdigit():
                value_str = str(value)
            else:
                # value-r modde single quote (') thakle (jemon "O'Brien")
                # seta escape kora dorkar, na hole SQL bhenge jabe
                safe_value = str(value).replace("'", "''")
                value_str = "'" + safe_value + "'"

            conditions.append(f["column"] + " " + f["operator"] + " " + value_str)

        sql += " WHERE " + " AND ".join(conditions)

    return sql


# Quick test
if __name__ == "__main__":
    schema = {
        "Age": {"dtype": "int64", "sample_values": [30, 40]},
        "Gender": {"dtype": "object", "sample_values": ["Male", "Female"]},
        "District": {"dtype": "object", "sample_values": ["Dhaka", "Sylhet"]},
    }

    q = "show female patients older than 30 from dhaka"
    query = build_query(q, schema, "SELECT")
    print("Query:", query)
    print("SQL:", query_to_sql(query))

    q2 = "average age"
    query2 = build_query(q2, schema, "AVG")
    print("Query2:", query2)
    print("SQL2:", query_to_sql(query2))
