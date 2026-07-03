"""
train_intent.py

Kaj: intent_dataset.csv theke data niye ekta ML model train kora,
jeta user er question dekhe bolte parbe eta SELECT/COUNT/AVG/MAX/MIN/SUM
er modde kon intent.

Model: TF-IDF (text -> number) + Naive Bayes (classification)
Eta simple ebong choto dataset e valo kaj kore.
"""

import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


def train_and_save(csv_path="training_data/intent_dataset.csv",
                    model_path="models/intent_model.pkl",
                    vectorizer_path="models/vectorizer.pkl"):

    # Step 1: Dataset load kora
    data = pd.read_csv(csv_path)
    questions = data["question"]
    intents = data["intent"]

    # Step 2: Train/test bhag kora (test দিয়ে accuracy check korbo)
    x_train, x_test, y_train, y_test = train_test_split(
        questions, intents, test_size=0.2, random_state=42
    )

    # Step 3: Text ke number e convert kora (TF-IDF)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    x_train_vec = vectorizer.fit_transform(x_train)
    x_test_vec = vectorizer.transform(x_test)

    # Step 4: Model train kora
    model = MultinomialNB()
    model.fit(x_train_vec, y_train)

    # Step 5: Accuracy check kora
    predictions = model.predict(x_test_vec)
    accuracy = accuracy_score(y_test, predictions)
    print("Test accuracy:", round(accuracy * 100, 2), "%")

    # Step 6: Model ebong vectorizer save kora
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    with open(vectorizer_path, "wb") as f:
        pickle.dump(vectorizer, f)

    print("Model save hoise:", model_path)
    print("Vectorizer save hoise:", vectorizer_path)


if __name__ == "__main__":
    train_and_save()
