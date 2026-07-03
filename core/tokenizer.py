"""
tokenizer.py

Kaj: User er natural language question ke chhoto chhoto
token (word) e bhag kora, ebong stopwords (show, list, the, a, ...)
bad deya.

Example:
  Input:  "Show female patients older than 30"
  Output: ["female", "patients", "older", "than", "30"]
"""

import os
import re
import json


def load_stopwords(path="knowledge/stopwords.json"):
    """Stopwords list load kore. File na paile empty list dey."""
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        stopwords = json.load(f)

    return stopwords


def clean_text(text):
    """Text ke lowercase kore ebong extra symbol (,.!? etc) shorai."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text, stopwords_path="knowledge/stopwords.json"):
    """
    Main function: question ke clean kore, token e bhag kore,
    ebong stopwords bad diye chhoto list return kore.
    """
    stopwords = load_stopwords(stopwords_path)
    cleaned = clean_text(text)
    tokens = cleaned.split()

    tokens = [t for t in tokens if t not in stopwords]

    return tokens


# Quick test
if __name__ == "__main__":
    question = "Show me all female patients older than 30 from Dhaka"
    result = tokenize(question, "../knowledge/stopwords.json")
    print("Original:", question)
    print("Tokens:", result)
