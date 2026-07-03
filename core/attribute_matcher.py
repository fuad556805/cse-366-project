"""
attribute_matcher.py

Kaj: Question-er word (jemon "years", "credit score") dekhe
dataset-er schema-r sothik column ta (jemon "Age", "CreditScore") khuje ber kora.

Improvements:
- Underscore <-> space normalization: "credit score" → "credit_score" match hoy.
- Synonym lookup ekhon normalized column name-er sathe match kore.
- Bigram + trigram support — multi-word column names detect kore.
"""

import os
import re
import json
from rapidfuzz import process, fuzz


def load_synonyms(path="knowledge/synonyms.json"):
    """synonyms.json load kore. File na paile empty dict return kore."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # "_comment" key remove koro jodi thake
    data.pop("_comment", None)
    return data


def _normalize(text):
    """
    Underscore ke space diye replace kore, lowercase kore.
    "credit_score" -> "credit score", "MarketValue" -> "marketvalue" (no change for camel)
    """
    return text.lower().replace("_", " ").strip()


def _build_lookup(schema):
    """
    Schema theke normalized lowercase column name -> original column name mapping banay.
    Both original and underscore-normalized versions stored.
    """
    lookup = {}
    for col in schema.keys():
        # Original lowercase
        lookup[col.lower()] = col
        # Underscore -> space normalized
        normalized = _normalize(col)
        if normalized not in lookup:
            lookup[normalized] = col
    return lookup


def match_column(word, schema, synonyms_path="knowledge/synonyms.json", threshold=70):
    """
    Ekta single word (ba phrase) dekhe schema-r kon column-er sathe match kore.
    Match na pele None return kore.

    Steps:
    1. Direct fuzzy match: normalized word vs normalized column names
    2. Synonym lookup: word -> canonical term -> fuzzy match vs column names
    """
    if not word or not schema:
        return None

    synonyms = load_synonyms(synonyms_path)
    word_norm = _normalize(word)

    lower_to_original = _build_lookup(schema)
    lower_columns = list(lower_to_original.keys())

    # Step 1: Direct fuzzy match (token_sort_ratio handles word-order better)
    result = process.extractOne(
        word_norm, lower_columns, scorer=fuzz.token_sort_ratio
    )
    if result and result[1] >= threshold:
        return lower_to_original[result[0]]

    # Step 2: Synonym lookup then fuzzy match
    if word_norm in synonyms:
        synonym_norm = _normalize(synonyms[word_norm])
        result = process.extractOne(
            synonym_norm, lower_columns, scorer=fuzz.token_sort_ratio
        )
        if result and result[1] >= threshold:
            return lower_to_original[result[0]]

    # Step 3: Also try original word (before normalization) in synonyms
    word_lower = word.lower().strip()
    if word_lower in synonyms:
        synonym_norm = _normalize(synonyms[word_lower])
        result = process.extractOne(
            synonym_norm, lower_columns, scorer=fuzz.token_sort_ratio
        )
        if result and result[1] >= threshold:
            return lower_to_original[result[0]]

    return None


def find_columns_in_text(text, schema, synonyms_path="knowledge/synonyms.json"):
    """
    Pura question theke shob shomvabbo matched column ber kore (duplicate bad diye).

    Single word, bigram (2 consecutive words) ebong trigram (3 consecutive words)
    shob-i try kora hoy — jate multi-word column name ("First Name",
    "Market Value", "Credit Score") o detect hoy.
    """
    words = text.lower().split()
    matched = []

    # n-gram size: 3 theke shuru kore smaller n-te jao (longer match priority)
    for n in (3, 2, 1):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i: i + n])
            column = match_column(phrase, schema, synonyms_path)
            if column and column not in matched:
                matched.append(column)

    return matched


# Quick test
if __name__ == "__main__":
    schema = {
        "Age":          {"dtype": "int64",   "sample_values": [30, 40]},
        "Gender":       {"dtype": "object",  "sample_values": ["Male", "Female"]},
        "CreditScore":  {"dtype": "int64",   "sample_values": [700, 650]},
        "MarketValue":  {"dtype": "float64", "sample_values": [1.5, 2.0]},
        "District":     {"dtype": "object",  "sample_values": ["Dhaka"]},
    }
    tests = [
        ("credit score",  "CreditScore"),
        ("market value",  "MarketValue"),
        ("years",         "Age"),
        ("sex",           "Gender"),
    ]
    syn_path = "../knowledge/synonyms.json"
    for word, expected in tests:
        got = match_column(word, schema, syn_path)
        status = "OK" if got == expected else "FAIL"
        print(f"[{status}] '{word}' -> {got} (expected {expected})")
