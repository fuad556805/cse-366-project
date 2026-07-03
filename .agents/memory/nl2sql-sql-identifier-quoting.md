---
name: nl2sql SQL identifier quoting
description: Generator quotes all SQL identifiers with double-quotes; tests and validator must match
---

## Rule
`query_to_sql()` in `core/sql_generator.py` wraps ALL column names and table names in double-quotes using `_quote_identifier()`. This was introduced to support multi-word column names (e.g. "First Name").

Example output: `SELECT * FROM "data" WHERE "Gender" = 'Female' AND "Age" > 30`

**Why:** Without quoting, multi-word column names produce invalid SQL (`First Name = 'x'` is a syntax error). Double-quoting is the SQL standard for identifiers.

**How to apply:**
- Any test asserting SQL output must use the quoted form: `'"Gender" = \'Female\''` not `"Gender = 'Female'"`
- `sql_validator.py` checks for both `table_name` and `"table_name"` in the SQL (handles quoted table)
- `sql_validator.py` WHERE-column regex handles `"quoted"`, `` `backtick` ``, and bare identifiers
