"""
sql_validator.py

Kaj: Generated SQL query execute korar age check kora eta safe ebong
sothik kina.

Checks:
1. SELECT diye shuru hoa (non-SELECT block)
2. Dangerous keyword na thaka
3. Multiple statement (semicolon injection) na thaka
4. Sothik table name use hoa
5. WHERE clause-er column gula schema-te thaka

Bug fixes (v2):
- Dangerous keyword check ekhon quoted string literal-er bhitor keyword
  search kore na — prothome string literal strip kore tarpor check kore.
  Agey `note = 'drop box'` type valid query block hoto, ekhon hoy na.
- Column regex: unquoted, double-quoted (multi-word column name support),
  ebong backtick-quoted identifiers shob handle kore.
- Table name check: quoted table name-o handle kore (generator ekhon
  double-quote use kore).
"""

import re


DANGEROUS_KEYWORDS = [
    "drop", "delete", "update", "insert", "alter",
    "attach", "detach", "pragma", "create",
]


def _strip_string_literals(sql):
    """
    SQL theke single-quoted string literal gula remove kore (placeholder diye replace).
    Eta dangerous keyword check-er age kora hoy, jate valid categorical value-er
    modhye keyword thakle false positive na hoy.

    Example: `Gender = 'drop'`  →  `Gender = ''`
    """
    # Single-quoted string literal: '' (escaped quote inside) handle korche
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

    # Rule 2: Dangerous keyword check (string literals-er baireye shudhu)
    sql_no_literals     = _strip_string_literals(sql_stripped)
    sql_no_literals_low = sql_no_literals.lower()

    for keyword in DANGEROUS_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", sql_no_literals_low):
            return False, f"Dangerous keyword paoa gese: '{keyword}'. Query block kora holo."

    # Rule 3: Multiple statement block (semicolon injection)
    body = sql_stripped.rstrip(";")
    if ";" in body:
        return False, "Ekadhik SQL statement allowed na (extra semicolon paoa gese)."

    # Rule 4: Sothik table name check (strict word-boundary match)
    # Substring check use kora thik na — "data" in "metadata" True hoy,
    # jate bypass shomvob. Ekhon FROM / JOIN-er pore exact identifier
    # check kora hoy (double-quoted ba bare word, word boundary soho).
    table_lower = table_name.lower()
    # Strict exact-match check for the table name after FROM/JOIN.
    # Two alternatives:
    #   "tablename"  — double-quoted identifier (generator always emits this);
    #                  closing " is its own delimiter so no \b needed.
    #   tablename\b  — unquoted bare word; \b on the right prevents
    #                  "data" matching inside "metadata" or "data_backup".
    # The \b before (?:from|join) plus \s+ before the identifier
    # ensure the left side is also word-bounded for the bare alternative.
    _table_pattern = re.compile(
        r'\b(?:from|join)\s+(?:"' + re.escape(table_lower) + r'"|'
        + re.escape(table_lower) + r'\b)',
        re.IGNORECASE,
    )
    # sql_no_literals use kora hoy (sql_lower noy) jate string literal-er modhye
    # "from data" type phrase diye table check bypass kora na jay.
    if not _table_pattern.search(sql_no_literals):
        return False, f"Table name '{table_name}' query-te paoa jay nai."

    # Rule 5: WHERE clause-er column schema-te ache kina
    valid_columns_lower = {c.lower() for c in schema.keys()}
    where_match = re.search(r"\bwhere\b(.+)$", sql_stripped,
                            re.IGNORECASE | re.DOTALL)

    if where_match:
        where_clause = where_match.group(1)

        # String literal gula strip kore — jate value-r modhe "=" etc.
        # thakle false column match na hoy
        where_no_literals = _strip_string_literals(where_clause)

        # Column identifier patterns:
        # 1. "quoted identifier"  — multi-word support
        # 2. `backtick identifier`
        # 3. bare_word            — simple alphanumeric
        col_pattern = re.compile(
            r'(?:"([^"]+)"|`([^`]+)`|([A-Za-z_][A-Za-z0-9_]*))'
            r'\s*(?:=|!=|<>|>=|<=|>|<|\bLIKE\b|\bBETWEEN\b|\bIS\b)',
            re.IGNORECASE,
        )

        for m in col_pattern.finditer(where_no_literals):
            col_name = (m.group(1) or m.group(2) or m.group(3) or "").strip()
            if not col_name:
                continue
            if col_name.lower() not in valid_columns_lower:
                return False, f"Column '{col_name}' schema-te paoa jay nai."

    return True, "SQL valid ache."


# Quick test
if __name__ == "__main__":
    schema = {
        "Age":      {"dtype": "int64",  "sample_values": [30]},
        "Gender":   {"dtype": "object", "sample_values": ["Female"]},
        "Notes":    {"dtype": "object", "sample_values": ["drop box"]},
        "First Name": {"dtype": "object", "sample_values": ["Rahim"]},
    }

    tests = [
        ('SELECT * FROM "data" WHERE "Age" > 30 AND "Gender" = \'Female\'', schema, True),
        ('SELECT * FROM "data" WHERE "Notes" = \'drop box\'',               schema, True),
        ('DROP TABLE data;',                                                 schema, False),
        ('SELECT * FROM "data" WHERE "Salary" > 1000',                      schema, False),
        ('SELECT * FROM "data"; DELETE FROM "data";',                        schema, False),
        ('SELECT COUNT(*) FROM "data"',                                      schema, True),
        ('SELECT * FROM "data" WHERE "Age" BETWEEN 20 AND 30',              schema, True),
        ('SELECT * FROM "data" WHERE "First Name" = \'Rahim\'',             schema, True),
    ]

    for sql, sch, expected in tests:
        valid, msg = validate_sql(sql, sch)
        status = "OK" if valid == expected else "FAIL"
        print(f"[{status}] valid={valid} | {msg[:60]}")
        print(f"       SQL: {sql[:70]}")
