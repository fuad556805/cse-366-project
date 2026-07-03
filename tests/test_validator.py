"""
test_validator.py

sql_validator module test kora.

Note: sql_generator ekhon double-quoted identifiers use kore.
Validator tests shei format-e update kora hoise.
Additional tests added:
- String literal-e dangerous keyword thakle valid howa uchit
- BETWEEN operator valid howa uchit
- Multi-word column name valid howa uchit
"""

from sql_validator import validate_sql


SCHEMA = {
    "Age":        {"dtype": "int64",  "sample_values": [30]},
    "Gender":     {"dtype": "object", "sample_values": ["Female"]},
    "Notes":      {"dtype": "object", "sample_values": ["drop box"]},
    "First Name": {"dtype": "object", "sample_values": ["Rahim"]},
}


def test_valid_select_query():
    is_valid, _ = validate_sql(
        'SELECT * FROM "data" WHERE "Age" > 30 AND "Gender" = \'Female\'',
        SCHEMA,
    )
    assert is_valid is True


def test_non_select_query_blocked():
    is_valid, message = validate_sql("DROP TABLE data;", SCHEMA)
    assert is_valid is False
    assert "SELECT" in message


def test_dangerous_keyword_blocked():
    is_valid, message = validate_sql(
        'SELECT * FROM "data"; DELETE FROM "data";', SCHEMA
    )
    assert is_valid is False
    assert "delete" in message.lower()


def test_unknown_column_blocked():
    is_valid, message = validate_sql(
        'SELECT * FROM "data" WHERE "Salary" > 1000', SCHEMA
    )
    assert is_valid is False
    assert "Salary" in message


def test_wrong_table_name_blocked():
    is_valid, message = validate_sql(
        'SELECT * FROM "other_table" WHERE "Age" > 30', SCHEMA, table_name="data"
    )
    assert is_valid is False


def test_keyword_in_string_literal_is_allowed():
    """
    Categorical value-er modhye dangerous keyword thakle (jemon 'drop box')
    query valid howa uchit — agey false positive hoto.
    """
    is_valid, _ = validate_sql(
        'SELECT * FROM "data" WHERE "Notes" = \'drop box\'',
        SCHEMA,
    )
    assert is_valid is True


def test_between_operator_is_valid():
    is_valid, _ = validate_sql(
        'SELECT * FROM "data" WHERE "Age" BETWEEN 20 AND 30',
        SCHEMA,
    )
    assert is_valid is True


def test_multiword_column_name_is_valid():
    is_valid, _ = validate_sql(
        'SELECT * FROM "data" WHERE "First Name" = \'Rahim\'',
        SCHEMA,
    )
    assert is_valid is True


def test_count_query_no_where():
    is_valid, _ = validate_sql(
        'SELECT COUNT(*) FROM "data"',
        SCHEMA,
    )
    assert is_valid is True


# ── Table-name bypass regression tests ────────────────────────────────────────

def test_table_name_substring_not_accepted():
    """'data' is a substring of 'metadata' — must NOT be accepted."""
    is_valid, msg = validate_sql(
        'SELECT * FROM metadata WHERE "Age" > 30',
        SCHEMA,
        table_name="data",
    )
    assert is_valid is False
    assert "data" in msg.lower()


def test_table_name_prefix_not_accepted():
    """'data_backup' starts with 'data' — must NOT be accepted."""
    is_valid, _ = validate_sql(
        'SELECT * FROM data_backup WHERE "Age" > 30',
        SCHEMA,
        table_name="data",
    )
    assert is_valid is False


def test_table_name_quoted_wrong_not_accepted():
    """Quoted wrong table name must NOT be accepted."""
    is_valid, _ = validate_sql(
        'SELECT * FROM "mydata" WHERE "Age" > 30',
        SCHEMA,
        table_name="data",
    )
    assert is_valid is False


def test_table_name_exact_bare_accepted():
    """Exact unquoted table name must be accepted."""
    is_valid, _ = validate_sql(
        "SELECT * FROM data WHERE \"Age\" > 30",
        SCHEMA,
        table_name="data",
    )
    assert is_valid is True


def test_table_name_exact_quoted_accepted():
    """Exact double-quoted table name (generator default) must be accepted."""
    is_valid, _ = validate_sql(
        'SELECT AVG("Age") FROM "data"',
        SCHEMA,
        table_name="data",
    )
    assert is_valid is True


def test_table_name_spoofed_via_string_literal_blocked():
    """
    String literal-e 'from data' thakle wrong table accept howa uchit na.
    Agey sql_lower-e search korle bypass shomvob hoto.
    """
    is_valid, _ = validate_sql(
        "SELECT * FROM other WHERE \"Notes\" = 'from data'",
        SCHEMA,
        table_name="data",
    )
    assert is_valid is False
