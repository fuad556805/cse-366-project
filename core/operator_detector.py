"""
operator_detector.py

Kaj: Natural language question theke SQL operator (>, <, =, ...) detect kora.

Bug fixes:
- Agey shudhu text_lower.find(phrase) diye PROTHOM occurrence detect hoto.
  Ekhon re.finditer diye SHOB occurrence detect hoy.
- Position tracking improve kora hoise: akta phrase ja positions cover kore
  shob position mark kora hoy, jate overlapping / conflict na hoy.
  (Agey shudhu start position mark hoto — phrase-er baki character gula
  onno shorter phrase-er sathe conflict korto.)
"""

import re
import json


def load_operators(path="knowledge/operators.json"):
    """operators.json theke phrase -> symbol mapping load kore."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_operators(text, operators_path="knowledge/operators.json"):
    """
    Question theke shob SQL operator detect kore, position soho.

    Return: [{"symbol": ">", "position": 10}, ...]
    Position mane phrase-er character start index in the original text.

    Longest phrase first check kora hoy jate "greater than or equal to"
    "greater than"-er age-i match hoy.
    """
    operators = load_operators(operators_path)
    text_lower = text.lower()

    # Longest phrase first (greedy matching)
    sorted_phrases = sorted(operators.keys(), key=len, reverse=True)

    found = []
    # Shob used character position track korbo jate overlap na hoy
    used_positions = set()

    for phrase in sorted_phrases:
        phrase_len = len(phrase)

        # text-e ei phrase-er shob occurrence khoja
        for match in re.finditer(re.escape(phrase), text_lower):
            start = match.start()
            end = match.end()  # exclusive

            # Ei range-er kono position already used kina check kora
            positions_needed = set(range(start, end))
            if positions_needed & used_positions:
                # Overlap ache — skip
                continue

            # Word boundary check: phrase-er age o pore space/start/end thaka dorkar,
            # jate "not" phrase "cannot"-er modhe bhul kore match na kore
            char_before = text_lower[start - 1] if start > 0 else " "
            char_after = text_lower[end] if end < len(text_lower) else " "

            if not (char_before in (" ", "\t") or start == 0):
                continue
            if not (char_after in (" ", "\t") or end == len(text_lower)):
                continue

            found.append({"symbol": operators[phrase], "position": start})
            used_positions.update(positions_needed)

    # Position onujayi sort kora
    found.sort(key=lambda item: item["position"])
    return found
