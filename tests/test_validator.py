"""
test_validator.py

sql_validator module test kora.
"""

from sql_validator import validate_sql


SCHEMA = {
    "Age": {"dtype": "int64", "sample_values": [30]},
    "Gender": {"dtype": "object", "sample_values": ["Female"]},
}


def test_valid_select_query():
    is_valid, _ = validate_sql(
        "SELECT * FROM data WHERE Age > 30 AND Gender = 'Female'", SCHEMA
    )
    assert is_valid is True


def test_non_select_query_blocked():
    is_valid, message = validate_sql("DROP TABLE data;", SCHEMA)
    assert is_valid is False
    assert "SELECT" in message


def test_dangerous_keyword_blocked():
    is_valid, message = validate_sql(
        "SELECT * FROM data; DELETE FROM data;", SCHEMA
    )
    assert is_valid is False
    assert "delete" in message.lower()


def test_unknown_column_blocked():
    is_valid, message = validate_sql(
        "SELECT * FROM data WHERE Salary > 1000", SCHEMA
    )
    assert is_valid is False
    assert "Salary" in message


def test_wrong_table_name_blocked():
    is_valid, message = validate_sql(
        "SELECT * FROM other_table WHERE Age > 30", SCHEMA, table_name="data"
    )
    assert is_valid is False
