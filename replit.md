# nl2sql_ai

A hybrid NL-to-SQL AI written in Python. Converts natural language questions into SQL queries using a combination of ML (intent classification) and rule-based (operator/attribute/value matching) approaches. Works with any user-supplied CSV dataset.

## How to run

### Web application (default — runs in browser)

```bash
# Install dependencies
pip install -r requirements.txt

# Start the Flask web server
python app.py
```

Open the app in your browser. Upload any CSV, then type a plain-English question and click **Ask**.

### CLI (original interactive mode)

```bash
python3 main.py
```

You will be prompted for a CSV file path, then can ask natural-language questions about it. Type `exit` to quit, `change_csv` to switch datasets.

## How to retrain the intent model

```bash
python3 training_data/generate_dataset.py   # regenerate intent_dataset.csv
python3 models/train_intent.py              # retrain model + vectorizer
```

## How to run tests

```bash
python -m pytest tests/ -v
```

27 tests cover: dataset loading, schema reading, attribute matching, value matching, operator detection, SQL generation, SQL execution, and SQL validation.

## Architecture

```
CSV Upload
   │
dataset_loader.py   — CSV → pandas DataFrame → SQLite
schema_reader.py    — Extract column names, dtypes, sample values (up to 100)
   │
intent_detector.py  — TF-IDF + Naive Bayes → SELECT / COUNT / AVG / MAX / MIN / SUM
operator_detector.py— Rule-based phrase matching → SQL operator symbol + position
attribute_matcher.py— Fuzzy match + synonyms (single/bigram/trigram) → column name
value_matcher.py    — Regex (numbers) + schema sample matching (categoricals)
   │
sql_generator.py    — Compose internal query dict → SQL string (quoted identifiers)
sql_validator.py    — Safety + column existence check (strips string literals first)
sql_executor.py     — Execute SQL against SQLite → (columns, rows)
response.py         — Format results as aligned ASCII table
```

## Project structure

```
nl2sql_ai/
├── main.py                         — Interactive CLI pipeline
├── requirements.txt
├── data/
│   ├── sample.csv                  — Patient demo dataset (10 rows)
│   ├── students.csv                — Student demo dataset (10 rows)
│   └── database.db                 — Auto-generated from CSV
├── models/
│   ├── train_intent.py             — Train intent classifier
│   ├── intent_model.pkl            — Pre-trained Naive Bayes model
│   └── vectorizer.pkl              — Pre-trained TF-IDF vectorizer
├── core/                           — Pipeline modules
├── knowledge/
│   ├── operators.json              — NL phrase → SQL operator mapping
│   ├── synonyms.json               — Word → canonical column-name mapping
│   └── stopwords.json              — Words to strip before tokenization
├── training_data/                  — Intent training data + generation scripts
└── tests/                          — pytest suite (27 tests)
```

## User preferences

- Pure Python CLI only — no web UI, no HTML/CSS/JS, no frameworks
- Existing project structure must be preserved (no renames, no new top-level modules)
- Code must be dataset-independent (no hardcoded column names or dataset-specific logic)
- Comments in Bengali (Bangla) are part of the project style — keep them
