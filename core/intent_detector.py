"""
intent_detector.py

Kaj: Train kora model + vectorizer load kore,
user er question dekhe intent (SELECT/COUNT/AVG/MAX/MIN/SUM) predict kora.

Post-processing overrides (rule-based correction):
- "show / list / display / give me / find all" -> SELECT
  (jodi "count / how many / total number" na thake)
- "top N / bottom N / lowest N / best N" -> SELECT
  (ORDER BY + LIMIT use hobe, aggregate na)
"""

import re
import pickle

# "show/list/display" trigger word gula (COUNT/AVG keyword na thakle)
_SHOW_TRIGGERS = re.compile(
    r"\b(show|list|display|give me|find all|get all|fetch|retrieve|return)\b",
    re.IGNORECASE,
)
_COUNT_OVERRIDES = re.compile(
    r"\b(count|how many|number of|total number)\b",
    re.IGNORECASE,
)

# "top N / bottom N / lowest N" pattern — ei gula SELECT + ORDER BY howa uchit
_RANK_TRIGGERS = re.compile(
    r"\b(top|bottom|lowest|least|worst|best)\s+\d+\b",
    re.IGNORECASE,
)


def _override_intent(text, ml_intent):
    """
    ML model-er prediction ke rule-based logic diye correct kore.
    Override na dorkhar hole same intent return kore.
    """
    # Rule 1: "top N / bottom N" type question -> SELECT (ORDER BY+LIMIT hobe)
    if _RANK_TRIGGERS.search(text):
        return "SELECT"

    # Rule 2: "show/list/display/..." keyword thakle -> SELECT
    # (jodi same question e "how many / count" na thake)
    if _SHOW_TRIGGERS.search(text) and not _COUNT_OVERRIDES.search(text):
        return "SELECT"

    return ml_intent


def load_model(model_path="models/intent_model.pkl",
                vectorizer_path="models/vectorizer.pkl"):
    """Save kora model ebong vectorizer load kore."""
    with open(model_path, "rb") as f:
        model = pickle.load(f)

    with open(vectorizer_path, "rb") as f:
        vectorizer = pickle.load(f)

    return model, vectorizer


def predict_intent(text, model, vectorizer):
    """
    Question theke intent predict kore (SELECT, COUNT, AVG, MAX, MIN, SUM).
    ML model predict kore, tarpor rule-based override check hoy.
    """
    text_vec   = vectorizer.transform([text])
    ml_intent  = model.predict(text_vec)[0]
    return _override_intent(text, ml_intent)


# Quick test
if __name__ == "__main__":
    model, vectorizer = load_model("../models/intent_model.pkl", "../models/vectorizer.pkl")

    test_questions = [
        "show all patients older than 30",
        "how many students are from dhaka",
        "average marks of students",
        "highest salary",
        "lowest age",
        "total income",
    ]

    for q in test_questions:
        result = predict_intent(q, model, vectorizer)
        print(q, "->", result)
