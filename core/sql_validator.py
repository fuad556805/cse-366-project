"""
sql_validator.py

Kaj: Generated SQL query execute korar AGE check kora eta safe ebong
sothik kina. Duita jinis check kora hoy:

1. Safety - kono dangerous command (DROP, DELETE, UPDATE...) thakle
   seta block kora, jate bhul kore kokhono dataset nosto na hoy.
2. Correctness - WHERE clause-e je column gula use hoise shegula
   asholei dataset-er schema-te ache kina, thakle "no such column"
   error runtime-e na eshe age-i dhora pore.
"""

import re


DANGEROUS_KEYWORDS = [
    "drop", "delete", "update", "insert", "alter",
    "attach", "detach", "pragma", "create", "replace"
]


def validate_sql(sql, schema, table_name="data"):
    """
    SQL query validate kore.
    Return: (is_valid, message) - is_valid True/False, message reason.
    """
    sql_stripped = sql.strip()
    sql_lower = sql_stripped.lower()

    # Rule 1: shudhu SELECT query allow kora hoy, onno kichu na
    if not sql_lower.startswith("select"):
        return False, "Shudhu SELECT query allowed - query SELECT diye shuru hoy nai."

    # Rule 2: dangerous keyword thakle block kora
    for keyword in DANGEROUS_KEYWORDS:
        # \b diye word-boundary check korchi, jate "created_at" column
        # thakle "create" keyword-er sathe bhul kore match na kore
        if re.search(r"\b" + keyword + r"\b", sql_lower):
            return False, "Dangerous keyword paoa gese: '" + keyword + "'. Query bad deya holo."

    # Rule 3: ekadhik SQL statement (semicolon diye stacked query
    # injection) block kora
    body = sql_stripped.rstrip(";")
    if ";" in body:
        return False, "Ekadhik SQL statement allowed na (extra semicolon paoa gese)."

    # Rule 4: sothik table name use hoise kina check kora
    if table_name.lower() not in sql_lower:
        return False, "Table name '" + table_name + "' query-te paoa jay nai."

    # Rule 5: WHERE clause-e je column gula ache shegula schema-te
    # ache kina check kora (typo/bhul column dhorar jonno)
    valid_columns = [c.lower() for c in schema.keys()]
    where_match = re.search(r"where(.+)$", sql_stripped, re.IGNORECASE)

    if where_match:
        where_clause = where_match.group(1)
        condition_columns = re.findall(
            r"([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|>|<|>=|<=|!=)",
            where_clause
        )

        for column in condition_columns:
            if column.lower() not in valid_columns:
                return False, "Column '" + column + "' schema-te paoa jay nai."

    return True, "SQL valid ache."


# Quick test
if __name__ == "__main__":
    schema = {
        "Age": {"dtype": "int64", "sample_values": [30]},
        "Gender": {"dtype": "object", "sample_values": ["Female"]},
    }

    print(validate_sql("SELECT * FROM data WHERE Age > 30 AND Gender = 'Female'", schema))
    print(validate_sql("DROP TABLE data;", schema))
    print(validate_sql("SELECT * FROM data WHERE Salary > 1000", schema))
    print(validate_sql("SELECT * FROM data; DELETE FROM data;", schema))
