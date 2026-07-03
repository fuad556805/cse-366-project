"""
intent_detector.py

Kaj: Train kora model + vectorizer load kore,
user er question dekhe intent (SELECT/COUNT/AVG/MAX/MIN/SUM) predict kora.
"""

import pickle


def load_model(model_path="models/intent_model.pkl",
                vectorizer_path="models/vectorizer.pkl"):
    """Save kora model ebong vectorizer load kore."""
    with open(model_path, "rb") as f:
        model = pickle.load(f)

    with open(vectorizer_path, "rb") as f:
        vectorizer = pickle.load(f)

    return model, vectorizer


def predict_intent(text, model, vectorizer):
    """Question theke intent predict kore (jemon: SELECT, COUNT, AVG...)."""
    text_vec = vectorizer.transform([text])
    intent = model.predict(text_vec)[0]
    return intent


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
