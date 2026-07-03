# operator_detector.py

import json


def load_operators(path="knowledge/operators.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_operators(text, operators_path="knowledge/operators.json"):
   
    operators = load_operators(operators_path)
    text_lower = text.lower()

    sorted_phrases = sorted(operators.keys(), key=len, reverse=True)

    found = []
    used_positions = set()

    for phrase in sorted_phrases:
        start = text_lower.find(phrase)
        if start != -1 and start not in used_positions:
            found.append({"symbol": operators[phrase], "position": start})
            used_positions.add(start)

    found.sort(key=lambda item: item["position"])
    return found