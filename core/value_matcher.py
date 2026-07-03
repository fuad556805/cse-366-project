"""
value_matcher.py

Kaj: Question theke value ber kora - duita type-er value:
1. Number (jemon 30, 50) - regex diye ber kora
2. Categorical value (jemon "Female", "Dhaka") - schema-r sample
   value-r sathe mile dekhe ber kora
"""

import re


def extract_numbers(text):
    """Text theke shob number khuje ber kore, position soho."""
    numbers = []
    for match in re.finditer(r"\d+(\.\d+)?", text):
        numbers.append({"value": match.group(), "position": match.start()})
    return numbers


def match_categorical_values(text, schema):
    """
    Text-e schema-r kono column-er sample value (jemon 'Female', 'Dhaka')
    ache kina check kore. Thakle {"column": ..., "value": ...} pair return kore.
    """
    text_lower = text.lower()
    matches = []

    for column, info in schema.items():
        # numeric column (Age, Price...) er value ekhane check korbo na,
        # karon shegula operator diye (>, <, =) handle hobe, plain
        # text match korle "30" k bhul kore categorical value bhabte pare.
        if "int" in info["dtype"] or "float" in info["dtype"]:
            continue

        for sample in info["sample_values"]:
            sample_str = str(sample).lower()
            if not sample_str:
                continue

            # \b (word boundary) use korchi jate "female" er modde
            # "male" thakle bhul kore match na kore fele
            pattern = r"\b" + re.escape(sample_str) + r"\b"
            if re.search(pattern, text_lower):
                matches.append({"column": column, "value": str(sample)})

    return matches


# Quick test
if __name__ == "__main__":
    schema = {
        "Gender": {"dtype": "object", "sample_values": ["Male", "Female"]},
        "District": {"dtype": "object", "sample_values": ["Dhaka", "Sylhet"]},
    }
    q = "show female patients older than 30 from dhaka"
    print("Numbers:", extract_numbers(q))
    print("Categorical:", match_categorical_values(q, schema))
