"""
attribute_matcher.py

Kaj: Question-er kono word (jemon "years", "yrs", "sex") dekhe
dataset-er schema-r shathik column ta (jemon "Age", "Gender") khuje ber kora.

Eta dorkar karon amra jani na user kon dataset dibe - column name
jekono kichu hote pare, tai fuzzy matching + synonym use korchi.
"""

import json
from rapidfuzz import process, fuzz


def load_synonyms(path="knowledge/synonyms.json"):
    if not __import__("os").path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def match_column(word, schema, synonyms_path="knowledge/synonyms.json", threshold=70):
    """
    Ekta shingle word dekhe schema-r kon column-er sathe match kore
    seta ber kore. Match na pele None return kore.
    """
    synonyms = load_synonyms(synonyms_path)
    word_lower = word.lower()

    column_names = list(schema.keys())
    if not column_names:
        return None

    # case-sensitive problem avoid korar jonno shob column lowercase kore
    # compare korchi, tarpor original column name ta ber kore anchi.
    lower_to_original = {col.lower(): col for col in column_names}
    lower_columns = list(lower_to_original.keys())

    # Step 1: age direct word diye match try kora (jemon dataset e
    # column-er naam-i "Years" hoy tahole eta shorashori mile jabe)
    result = process.extractOne(word_lower, lower_columns, scorer=fuzz.ratio)
    if result and result[1] >= threshold:
        return lower_to_original[result[0]]

    # Step 2: direct match na pele synonym diye try kora
    # (jemon "older" -> "age", jekhane dataset e "Age" column ache)
    if word_lower in synonyms:
        synonym_word = synonyms[word_lower]
        result = process.extractOne(synonym_word, lower_columns, scorer=fuzz.ratio)
        if result and result[1] >= threshold:
            return lower_to_original[result[0]]

    return None


def find_columns_in_text(text, schema, synonyms_path="knowledge/synonyms.json"):
    """Pura question theke shob shonvabbo matched column ber kore (duplicate bad diye)."""
    words = text.lower().split()
    matched = []

    for word in words:
        column = match_column(word, schema, synonyms_path)
        if column and column not in matched:
            matched.append(column)

    return matched


# Quick test
if __name__ == "__main__":
    schema = {
        "Age": {"dtype": "int64", "sample_values": [30, 40]},
        "Gender": {"dtype": "object", "sample_values": ["Male", "Female"]},
        "District": {"dtype": "object", "sample_values": ["Dhaka"]},
    }
    print(match_column("years", schema, "../knowledge/synonyms.json"))
    print(match_column("sex", schema, "../knowledge/synonyms.json"))
    print(find_columns_in_text("show patients with age and city", schema, "../knowledge/synonyms.json"))
