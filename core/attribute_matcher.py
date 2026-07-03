"""
attribute_matcher.py

Kaj: Question-er word (jemon "years", "yrs", "sex") dekhe
dataset-er schema-r sothik column ta (jemon "Age", "Gender") khuje ber kora.

Bug fixes:
- Agey shudhu single word match hoto. Ekhon bigram (2-word) ebong
  trigram (3-word) o check kora hoy, jate "first name", "date of birth"
  type multi-word column name gula-o match kore.
- load_synonyms path handling improve kora hoise: file na paile
  empty dict return kore, crash hoy na.
"""

import os
import json
from rapidfuzz import process, fuzz


def load_synonyms(path="knowledge/synonyms.json"):
    """synonyms.json load kore. File na paile empty dict return kore."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_lookup(schema):
    """
    Schema theke lowercase column name -> original column name mapping banay.
    Fuzzy matching-e lowercase compare kora hoy, then original name return kora hoy.
    """
    return {col.lower(): col for col in schema.keys()}


def match_column(word, schema, synonyms_path="knowledge/synonyms.json", threshold=70):
    """
    Ekta single word (ba phrase) dekhe schema-r kon column-er sathe match kore
    seta ber kore. Match na pele None return kore.

    Steps:
    1. Direct fuzzy match: word vs column names
    2. Synonym lookup: word -> canonical term -> fuzzy match vs column names
    """
    if not word or not schema:
        return None

    synonyms = load_synonyms(synonyms_path)
    word_lower = word.lower().strip()

    lower_to_original = _build_lookup(schema)
    lower_columns = list(lower_to_original.keys())

    # Step 1: Direct fuzzy match
    result = process.extractOne(word_lower, lower_columns, scorer=fuzz.ratio)
    if result and result[1] >= threshold:
        return lower_to_original[result[0]]

    # Step 2: Synonym lookup then fuzzy match
    if word_lower in synonyms:
        synonym_word = synonyms[word_lower].lower()
        result = process.extractOne(synonym_word, lower_columns, scorer=fuzz.ratio)
        if result and result[1] >= threshold:
            return lower_to_original[result[0]]

    return None


def find_columns_in_text(text, schema, synonyms_path="knowledge/synonyms.json"):
    """
    Pura question theke shob shomvabbo matched column ber kore (duplicate bad diye).

    Single word, bigram (2 consecutive words) ebong trigram (3 consecutive words)
    shob-i try kora hoy — jate multi-word column name (jemon "First Name",
    "Date Of Birth") o detect hoy.
    """
    words = text.lower().split()
    matched = []

    # n-gram size: 1 (single), 2 (bigram), 3 (trigram)
    for n in (1, 2, 3):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i: i + n])
            column = match_column(phrase, schema, synonyms_path)
            if column and column not in matched:
                matched.append(column)

    return matched


# Quick test
if __name__ == "__main__":
    schema = {
        "Age": {"dtype": "int64", "sample_values": [30, 40]},
        "Gender": {"dtype": "object", "sample_values": ["Male", "Female"]},
        "District": {"dtype": "object", "sample_values": ["Dhaka"]},
        "First Name": {"dtype": "object", "sample_values": ["Rahim"]},
    }
    print(match_column("years", schema, "../knowledge/synonyms.json"))
    print(match_column("sex", schema, "../knowledge/synonyms.json"))
    print(match_column("first name", schema, "../knowledge/synonyms.json"))
    print(find_columns_in_text("show patients with age and city", schema, "../knowledge/synonyms.json"))
    print(find_columns_in_text("show first name of all patients", schema, "../knowledge/synonyms.json"))
