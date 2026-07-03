"""
sql_validator.py

Kaj: Generated SQL query execute korar age check kora eta safe ebong
sothik kina.

Checks:
1. SELECT diye shuru hoa
2. Dangerous keyword na thaka (string literal-er baireye)
3. Multiple statement (semicolon injection) na thaka
4. Sothik table name use hoa
5. WHERE clause-er column gula schema-te thaka

v3 update:
- WHERE regex ekhon GROUP BY / ORDER BY-er age stop kore,
  jate sei clause-er column gula false-positive na dey.
"""

import re


DANGEROUS_KEYWORDS = [
    "drop", "delete", "update", "insert", "alter",
    "attach", "detach", "pragma", "create", "truncate",
]


def _strip_string_literals(sql):
    """Single-quoted string literal gula remove kore (placeholder diye replace)."""
    return re.sub(r"'(?:[^']|'')*'", "''", sql)


def validate_sql(sql, schema, table_name="data"):
    """
    SQL query validate kore.
    Return: (is_valid: bool, message: str)
    """
    sql_stripped = sql.strip()
    sql_lower    = sql_stripped.lower()

    # Rule 1: Shudhu SELECT query allowed
    if not sql_lower.startswith("select"):
        return False, "Shudhu SELECT query allowed — query SELECT diye shuru hoy nai."

    # Rule 2: Dangerous keyword check (string literals strip kore)
    sql_no_literals     = _strip_string_literals(sql_stripped)
    sql_no_literals_low = sql_no_literals.lower()

    for keyword in DANGEROUS_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", sql_no_literals_low):
            return False, f"Dangerous keyword paoa gese: '{keyword}'. Query block kora holo."

    # Rule 3: Multiple statement block
    body = sql_stripped.rstrip(";")
    if ";" in body:
        return False, "Ekadhik SQL statement allowed na (extra semicolon paoa gese)."

    # Rule 4: Table name check
    table_lower = table_name.lower()
    _table_pattern = re.compile(
        r'\b(?:from|join)\s+(?:"' + re.escape(table_lower) + r'"|'
        + re.escape(table_lower) + r'\b)',
        re.IGNORECASE,
    )
    if not _table_pattern.search(sql_no_literals):
        return False, f"Table name '{table_name}' query-te paoa jay nai."

    # Rule 5: WHERE clause-er column schema-te ache kina
    # WHERE theke GROUP BY / ORDER BY / LIMIT er age obdhi shudhu newa hoy
    valid_columns_lower = {c.lower() for c in schema.keys()}

    where_match = re.search(
        r"\bwhere\b(.+?)(?:\bgroup\s+by\b|\border\s+by\b|\blimit\b|$)",
        sql_stripped,
        re.IGNORECASE | re.DOTALL,
    )

    if where_match:
        where_clause = where_match.group(1)
        where_no_literals = _strip_string_literals(where_clause)

        col_pattern = re.compile(
            r'(?:"([^"]+)"|`([^`]+)`|([A-Za-z_][A-Za-z0-9_ ]*))'
            r'\s*(?:=|!=|<>|>=|<=|>|<|\bLIKE\b|\bBETWEEN\b|\bIS\b)',
            re.IGNORECASE,
        )

        for m in col_pattern.finditer(where_no_literals):
            col_name = (m.group(1) or m.group(2) or m.group(3) or "").strip()
            if not col_name:
                continue
            # AND / OR logical keywords skip
            if col_name.lower() in ("and", "or", "not"):
                continue
            if col_name.lower() not in valid_columns_lower:
                return False, f"Column '{col_name}' schema-te paoa jay nai."

    return True, "SQL valid ache."


# Quick test
if __name__ == "__main__":
    schema = {
        "Age":        {"dtype": "int64",  "sample_values": [30]},
        "Gender":     {"dtype": "object", "sample_values": ["Female"]},
        "Salary":     {"dtype": "float64","sample_values": [50000]},
        "Department": {"dtype": "object", "sample_values": ["CS"]},
        "Notes":      {"dtype": "object", "sample_values": ["drop box"]},
    }

    tests = [
        ('SELECT * FROM "data" WHERE "Age" > 30',                               True),
        ('SELECT * FROM "data" WHERE "Gender" = \'Female\' AND "Age" > 20',     True),
        ('SELECT "Department", AVG("Salary") FROM "data" GROUP BY "Department"',True),
        ('SELECT * FROM "data" ORDER BY "Salary" DESC LIMIT 10',                True),
        ('SELECT * FROM "data" WHERE "Notes" = \'drop box\'',                   True),
        ('DROP TABLE data;',                                                     False),
        ('SELECT * FROM "data" WHERE "Unknown" > 1000',                         False),
        ('SELECT * FROM "data"; DELETE FROM "data";',                            False),
    ]

    for sql, expected in tests:
        valid, msg = validate_sql(sql, schema)
        status = "OK" if valid == expected else "FAIL"
        print(f"[{status}] valid={valid} | {msg[:60]}")
        print(f"       SQL: {sql[:80]}")
