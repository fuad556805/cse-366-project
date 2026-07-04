"""
attribute_matcher.py

Kaj: Question-er word (jemon "years", "credit score") dekhe
dataset-er schema-r sothik column ta (jemon "Age", "CreditScore") khuje ber kora.

Improvements:
- Underscore <-> space normalization: "credit score" → "credit_score" match hoy.
- Synonym lookup ekhon normalized column name-er sathe match kore.
- Bigram + trigram support — multi-word column names detect kore.

v4 (bug fix — multi-word column jemon "Time Spent on Website (min)",
"Purchase Amount ($)", "Review Score (1-5)" thik moto detect na howa):
- _normalize() ekhon bracket-er bhitorer content ($, min, 1-5 etc) ebong
  symbol ($, %, -, etc) shoriye dey, jate "Purchase Amount ($)" ->
  "purchase amount" hoy.
- find_columns_with_positions() notun function — pura question-e stopword
  shoriye column-er word-count onujayi sliding window banie fuzzy match kore.
  Eta shudhu single word na, PURA column phrase ("time spent on website")
  ekshathe match kore, ebong result-e position soho dey jate sql_generator
  shobcheye kache-r column ta thik moto বেছে nite pare.
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


def load_stopwords(path="knowledge/stopwords.json"):
    """stopwords.json load kore. File na paile empty list return kore."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _strip_symbols(text):
    """
    Bracket-er bhitorer content shoriye dey (jemon "(min)", "($)", "(1-5)"),
    tarpor baki shob symbol ($, %, -, etc) shoriye shudhu letter/digit/space rakhe.
    """
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize(text):
    """
    Underscore ke space diye replace kore, bracket/symbol shoriye, lowercase kore.
    "credit_score" -> "credit score"
    "Purchase Amount ($)" -> "purchase amount"
    "Time Spent on Website (min)" -> "time spent on website"
    """
    text = text.lower().replace("_", " ")
    return _strip_symbols(text)


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


def find_columns_with_positions(text, schema,
                                 synonyms_path="knowledge/synonyms.json",
                                 stopwords_path="knowledge/stopwords.json",
                                 threshold=72):
    """
    Pura question theke matched column gula position + score soho ber kore.

    Purano version shudhu EKTA word (jemon "time", "spent", "website")
    dhore match korto — tai "Time Spent on Website (min)" er moto multi-word
    column detect korte parto na, ebong bhul kore onno numeric column
    (jemon "Customer ID") select hoye jeto.

    Notun logic:
    1. Question ebong column dutoi theke stopword ("the", "on", "of", ...)
       shoriye "core word" ber kora hoy.
    2. Prottek column-er core-word-count onujayi question-er core-word
       list-e shei size-er sliding window banano hoy, tarpor shei phrase-ta
       column-er core-phrase-er sathe fuzzy compare kora hoy.
       -> Eta pura multi-word column phrase-ke EKSHATHE match kore,
          filler word ("the", "on") thakleo problem hoy na.
    3. Fallback: jodi kono column exact-window-e match na kore, pura
       question-er against token_set_ratio try kora hoy (partial phrase,
       jemon "review" -> "Review Score") — kintu shudhu tokhon jokhon
       primary pass e kichu paoa jayni.

    Return: [{"column": "Age", "position": 10, "score": 100}, ...]
    (duplicate column hole shobcheye best score-walata rakha hoy)
    """
    if not text or not schema:
        return []

    synonyms = load_synonyms(synonyms_path)
    stopwords = set(load_stopwords(stopwords_path))

    raw_tokens = [
        {"word": m.group(), "position": m.start()}
        for m in re.finditer(r"[a-z0-9]+", text.lower())
    ]
    if not raw_tokens:
        return []

    core_tokens = [t for t in raw_tokens if t["word"] not in stopwords] or raw_tokens

    col_specs = []
    for col in schema.keys():
        norm = _normalize(col)
        if not norm:
            continue
        norm_words = norm.split()
        core_words = [w for w in norm_words if w not in stopwords] or norm_words
        col_specs.append({"column": col, "core_words": core_words,
                           "core_phrase": " ".join(core_words)})

    best_by_column = {}
    n_tokens = len(core_tokens)
    max_n = max((len(spec["core_words"]) for spec in col_specs), default=1)

    # ── Primary: exact-length sliding window match (multi-word phrase) ────
    for n in range(min(max_n, n_tokens), 0, -1):
        cols_of_size = [spec for spec in col_specs if len(spec["core_words"]) == n]
        if not cols_of_size:
            continue

        for i in range(n_tokens - n + 1):
            window = core_tokens[i:i + n]
            phrase = " ".join(t["word"] for t in window)
            phrase_pos = window[0]["position"]

            phrase_candidates = {phrase}
            if n == 1 and phrase in synonyms:
                phrase_candidates.add(_normalize(synonyms[phrase]))

            for spec in cols_of_size:
                score = max(
                    fuzz.token_sort_ratio(cand, spec["core_phrase"])
                    for cand in phrase_candidates
                )
                if score >= threshold:
                    prev = best_by_column.get(spec["column"])
                    if prev is None or score > prev["score"]:
                        best_by_column[spec["column"]] = {
                            "column": spec["column"],
                            "position": phrase_pos,
                            "score": score,
                        }

    # ── Fallback: partial-phrase match for columns not yet found ──────────
    question_core_phrase = " ".join(t["word"] for t in core_tokens)
    for spec in col_specs:
        if spec["column"] in best_by_column:
            continue
        score = fuzz.token_set_ratio(question_core_phrase, spec["core_phrase"])
        if score < max(threshold, 80):
            continue
        # Column-er first core-word question-e kothay ache seta position hisebe dhora
        position = None
        for token in core_tokens:
            for cw in spec["core_words"]:
                if fuzz.ratio(token["word"], cw) >= 85:
                    position = token["position"]
                    break
            if position is not None:
                break
        if position is None:
            position = core_tokens[0]["position"]

        best_by_column[spec["column"]] = {
            "column": spec["column"],
            "position": position,
            "score": score,
        }

    return sorted(best_by_column.values(), key=lambda r: (-r["score"], r["position"]))


def find_columns_in_text(text, schema, synonyms_path="knowledge/synonyms.json"):
    """
    Pura question theke shob shomvabbo matched column ber kore (duplicate bad diye).

    v4: multi-word phrase-o (jemon "Time Spent on Website (min)",
    "Purchase Amount ($)") ekhon thik moto detect hoy — dekho
    find_columns_with_positions().
    """
    matches = find_columns_with_positions(text, schema, synonyms_path)
    return [m["column"] for m in matches]


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
