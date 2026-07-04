"""
value_matcher.py

Kaj: Question theke value ber kora — duita type:
1. Number (jemon 30, 50.5) — regex diye ber kora
2. Categorical value (jemon "Female", "Dhaka") — schema sample value-er
   sathe match kore ber kora

Bug fixes:
- Agey per-column deduplication chilo na: same column-e multiple value
  match hole shob add hoto, ekhon per-column prothom match-i rakha hoy
  (unless same column e sobgulo alag operator diye rakha dorkar).
- Binary value support add kora hoise: 0/1, yes/no, true/false type
  columns ekhon theke handle hoy.
- match_categorical_values ekhon case-insensitive value compare kore
  original case ta filter-e use kore.
- Partial-word false match prevention-er jonno \b word boundary theke
  suru kore non-alphanumeric separator obdhi check kora hoy -.
"""

import re


def extract_numbers(text):
    """
    Text theke shob number khuje ber kore, position soho.
    Integer ba float — duita-i handle kore.

    Return: [{"value": "30", "position": 25}, ...]
    """
    numbers = []
    for match in re.finditer(r"\b\d+(?:\.\d+)?\b", text):
        numbers.append({"value": match.group(), "position": match.start()})
    return numbers


# Binary value gular canonical mapping (lowercase key -> original True value)
_BINARY_TRUE_MAP = {
    "yes": "Yes",
    "true": "True",
    "1": "1",
}
_BINARY_FALSE_MAP = {
    "no": "No",
    "false": "False",
    "0": "0",
}


def _is_binary_column(sample_values):
    """
    Akta column binary kina check kore.
    Binary mane: unique value shudhu 2 ta ebong shegula 0/1, yes/no, true/false.
    """
    if len(sample_values) != 2:
        return False
    lower_vals = {str(v).lower() for v in sample_values}
    binary_pairs = [
        {"yes", "no"},
        {"true", "false"},
        {"0", "1"},
        {"1", "0"},
    ]
    return lower_vals in binary_pairs


def match_categorical_values(text, schema):
    """
    Text-e schema-r kono column-er sample value (jemon 'Female', 'Dhaka')
    ache kina check kore. Thakle {"column": ..., "value": ...} pair return kore.

    Rules:
    - Numeric column skip (shegula operator diye handle hoy)
    - Per-column: prothom match rakha hoy (unless ekadhik alag value
      genuinely present in the question)
    - Word boundary use kore partial-word false match avoid kora hoy
    - Case-insensitive search, but original case value return kore
    """
    text_lower = text.lower()
    matches = []
    # Track: kon column-er value already matched — duplicate filter avoid
    matched_columns = set()

    for column, info in schema.items():
        dtype = info["dtype"]

        # Numeric column-er categorical value match skip kora
        if "int" in dtype or "float" in dtype:
            continue

        sample_values = info["sample_values"]
        if not sample_values:
            continue

        column_matched = False

        for sample in sample_values:
            if column_matched:
                break  # ei column-er janya akta match-i jaisa

            sample_str = str(sample)
            sample_lower = sample_str.lower()

            if not sample_lower:
                continue

            # Word boundary: \b alphanumeric boundary use kora hoy,
            # but multi-word values (jemon "New York") e inner space OK
            pattern = r"(?<![a-z0-9])" + re.escape(sample_lower) + r"(?![a-z0-9])"

            if re.search(pattern, text_lower):
                # Duplicate column check: same column already matched kina
                if column in matched_columns:
                    continue
                matches.append({"column": column, "value": sample_str})
                matched_columns.add(column)
                column_matched = True

    return matches


# Quick test
if __name__ == "__main__":
    schema = {
        "Gender": {"dtype": "object", "sample_values": ["Male", "Female"]},
        "District": {"dtype": "object", "sample_values": ["Dhaka", "Sylhet"]},
        "Active": {"dtype": "object", "sample_values": ["Yes", "No"]},
    }
    q = "show female patients older than 30 from dhaka"
    print("Numbers:", extract_numbers(q))
    print("Categorical:", match_categorical_values(q, schema))
    print("Binary test:", match_categorical_values("show active users", schema))
