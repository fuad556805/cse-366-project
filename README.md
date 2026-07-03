# nl2sql_ai — Natural Language to SQL Query Generation System

A hybrid AI system that converts plain English questions into executable SQL queries. It works with **any CSV dataset** — no hardcoded column names, no dataset-specific logic. Just upload a CSV and ask questions in English.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Objectives](#2-objectives)
3. [Technology Stack](#3-technology-stack)
4. [Architecture](#4-architecture)
5. [Pipeline Workflow](#5-pipeline-workflow)
6. [Folder Structure](#6-folder-structure)
7. [Module Reference](#7-module-reference)
8. [Algorithms & Techniques](#8-algorithms--techniques)
9. [Knowledge Files](#9-knowledge-files)
10. [Installation Guide](#10-installation-guide)
11. [Running the Program](#11-running-the-program)
12. [Dataset Handling](#12-dataset-handling)
13. [Model Training](#13-model-training)
14. [Testing](#14-testing)
15. [Example Session](#15-example-session)
16. [Limitations](#16-limitations)
17. [Future Improvements](#17-future-improvements)

---

## 1. Project Overview

**nl2sql_ai** is a command-line AI application that bridges the gap between human language and database queries. A user can type a question like:

```
show female patients older than 30 from Dhaka
```

and the system automatically generates and runs:

```sql
SELECT * FROM "data" WHERE "Gender" = 'Female' AND "Age" > 30 AND "District" = 'Dhaka'
```

then displays the result as a formatted table — all without the user knowing any SQL.

The system uses a **hybrid approach**:
- **Machine Learning** to understand *what the user wants* (intent classification)
- **Rule-based logic** to understand *which columns, operators, and values* are involved

This combination makes the system both flexible and interpretable.

---

## 2. Objectives

| # | Objective |
|---|-----------|
| 1 | Accept any user-uploaded CSV file as the dataset |
| 2 | Automatically detect the dataset schema (column names, data types, values) |
| 3 | Understand the user's intent: retrieve rows, count, average, max, min, or sum |
| 4 | Detect comparison operators from natural language ("older than" → `>`) |
| 5 | Match column names even when the user uses synonyms or abbreviations |
| 6 | Match categorical values (e.g. "Female", "Dhaka") from the actual dataset |
| 7 | Generate safe, valid SQL and execute it against a local SQLite database |
| 8 | Display results in a human-readable formatted table |
| 9 | Work entirely as a Python CLI — no web server, no UI framework |

---

## 3. Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.8+ | Primary programming language |
| **pandas** | latest | CSV loading, DataFrame operations |
| **SQLite** (built-in) | — | Lightweight database for query execution |
| **scikit-learn** | latest | TF-IDF vectorizer + Naive Bayes classifier for intent detection |
| **rapidfuzz** | latest | Fuzzy string matching for column name recognition |
| **pytest** | latest | Automated testing |
| **pickle** (built-in) | — | Saving and loading trained ML models |
| **re** (built-in) | — | Regular expressions for operator and value detection |
| **json** (built-in) | — | Loading knowledge files (operators, synonyms, stopwords) |

### Why these specific libraries?

**pandas** — The standard for tabular data in Python. Its `read_csv()` handles diverse CSV formats automatically, and `to_sql()` saves data to SQLite in one line.

**SQLite** — Requires no server, no installation, and no configuration. The entire database is a single file. Perfect for a local tool that needs to run SQL against uploaded datasets.

**scikit-learn** — Provides the TF-IDF vectorizer (converts text to numbers) and the Naive Bayes classifier (learns patterns from training examples). Both are lightweight, fast, and well-suited for short text classification.

**rapidfuzz** — A fast, production-quality fuzzy matching library. Used to match user words like "yrs" or "sex" to actual column names like "Age" or "Gender", even when the spelling is slightly different.

**pytest** — The standard Python testing framework. Clean syntax, automatic test discovery, and helpful failure output.

---

## 4. Architecture

The system is built as a **sequential pipeline** — each stage produces output that feeds into the next.

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Input                              │
│           "show female patients older than 30"                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. DATASET LOADING          dataset_loader.py                  │
│     CSV → pandas DataFrame → SQLite database                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. SCHEMA READING           schema_reader.py                   │
│     Extract: column names, data types, unique sample values     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                    ┌───────┴────────┐
                    │                │
                    ▼                ▼
        ┌───────────────┐  ┌─────────────────────┐
        │  3. INTENT    │  │  4. OPERATOR +       │
        │  DETECTION    │  │  ATTRIBUTE +         │
        │  (ML model)   │  │  VALUE MATCHING      │
        │               │  │  (rule-based)        │
        │  SELECT       │  │  Gender='Female'     │
        │  COUNT        │  │  Age > 30            │
        │  AVG/MAX/...  │  │                      │
        └───────┬───────┘  └──────────┬───────────┘
                │                     │
                └──────────┬──────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. SQL GENERATION           sql_generator.py                   │
│     Internal query dict → SQL string with quoted identifiers    │
│     SELECT * FROM "data" WHERE "Gender"='Female' AND "Age">30   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. SQL VALIDATION           sql_validator.py                   │
│     Safety check + column existence check                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. SQL EXECUTION            sql_executor.py                    │
│     Run SQL against SQLite → (column names, result rows)        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  8. RESPONSE FORMATTING      response.py                        │
│     Print result as a human-readable aligned ASCII table        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Pipeline Workflow

### Step 1 — Load the Dataset

The user provides a path to any CSV file. The system loads it into a pandas DataFrame and saves it to a local SQLite database file. This lets the system run standard SQL queries on it.

```python
df = load_dataset("data/sample.csv", "data/database.db", table_name="data")
```

### Step 2 — Read the Schema

The system inspects the DataFrame to extract metadata for every column:
- **Column name** (e.g. `Age`, `Gender`)
- **Data type** (numeric: `int64`/`float64`, or text: `object`)
- **Up to 100 unique sample values** (e.g. `["Male", "Female"]`)

This schema is used by all downstream matching steps. Nothing is hardcoded — the schema is discovered fresh from each dataset.

### Step 3 — Detect Intent (ML)

A pre-trained machine learning model reads the question and predicts **what type of SQL query** the user wants:

| Intent | Example Question | Generated SQL |
|--------|-----------------|---------------|
| `SELECT` | "show all patients from Dhaka" | `SELECT * FROM ...` |
| `COUNT` | "how many female patients are there" | `SELECT COUNT(*) FROM ...` |
| `AVG` | "average age of patients" | `SELECT AVG("Age") FROM ...` |
| `MAX` | "highest salary" | `SELECT MAX("Salary") FROM ...` |
| `MIN` | "lowest score" | `SELECT MIN("Score") FROM ...` |
| `SUM` | "total income" | `SELECT SUM("Income") FROM ...` |

### Step 4 — Detect Operators, Columns, and Values (Rule-based)

Three sub-components run in parallel on the question:

**Operator Detector** — scans for natural language phrases that imply comparison:

| Phrase | SQL Operator |
|--------|-------------|
| "older than", "greater than", "more than" | `>` |
| "younger than", "less than", "below" | `<` |
| "at least", "not less than" | `>=` |
| "at most", "no more than" | `<=` |
| "equal to", "is", "exactly" | `=` |
| "between" | `BETWEEN` |
| "is null", "is empty" | `IS NULL` |

**Attribute Matcher** — maps words in the question to actual column names using:
1. Fuzzy string matching (handles typos and abbreviations)
2. A synonym dictionary ("years" → age column, "sex" → gender column)
3. Bigram/trigram matching for multi-word column names ("first name", "date of birth")

**Value Matcher** — extracts filter values:
1. *Numeric values* — extracted by regex (`\b\d+(?:\.\d+)?\b`)
2. *Categorical values* — matched against the schema's sample values (e.g. "female" matches "Female" from the Gender column's sample values)

### Step 5 — Generate SQL

An internal dictionary representation is built first:

```python
{
    "intent": "SELECT",
    "filters": [
        {"column": "Gender", "operator": "=",  "value": "Female"},
        {"column": "Age",    "operator": ">",  "value": "30"},
        {"column": "District","operator": "=", "value": "Dhaka"}
    ],
    "agg_column": None
}
```

This is then converted to a SQL string. All column names and the table name are wrapped in **double-quotes** to handle multi-word column names correctly:

```sql
SELECT * FROM "data"
WHERE "Gender" = 'Female' AND "Age" > 30 AND "District" = 'Dhaka'
```

### Step 6 — Validate the SQL

Before execution, the SQL is checked for:
1. Must start with `SELECT` (no mutations allowed)
2. No dangerous keywords: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, etc.
   - String literals are stripped first so a value like `'drop box'` doesn't trigger a false block
3. No stacked statements (`;` injection blocked)
4. The correct table name must appear after `FROM` or `JOIN` (exact match, not substring)
   - Searched on literal-stripped SQL so `WHERE col = 'from data'` can't spoof the table name
5. All columns in the `WHERE` clause must exist in the schema

### Step 7 — Execute the SQL

The validated SQL is run against the SQLite database. The result is returned as a list of column names and a list of rows (tuples).

### Step 8 — Format and Display

Results are printed as a width-aware aligned table:

```
Name   | Age | Gender | District
---------------------------------------
Fatima | 28  | Female | Dhaka
Nusrat | 55  | Female | Chittagong
Sima   | 40  | Female | Sylhet
```

---

## 6. Folder Structure

```
nl2sql_ai/
│
├── main.py                        ← Entry point: interactive CLI loop
├── requirements.txt               ← Python dependencies
├── README.md                      ← This file
│
├── core/                          ← All pipeline modules
│   ├── dataset_loader.py          ← CSV loading + SQLite persistence
│   ├── schema_reader.py           ← Schema extraction from DataFrame
│   ├── tokenizer.py               ← Text cleaning + stopword removal
│   ├── intent_detector.py         ← ML model loading + intent prediction
│   ├── operator_detector.py       ← NL phrase → SQL operator mapping
│   ├── attribute_matcher.py       ← Fuzzy column name matching
│   ├── value_matcher.py           ← Number + categorical value extraction
│   ├── sql_generator.py           ← Internal query dict → SQL string
│   ├── sql_validator.py           ← SQL safety + correctness check
│   ├── sql_executor.py            ← SQLite query execution
│   └── response.py                ← Result table formatting
│
├── models/
│   ├── train_intent.py            ← Script to train the intent classifier
│   ├── intent_model.pkl           ← Pre-trained Naive Bayes model (binary)
│   └── vectorizer.pkl             ← Pre-trained TF-IDF vectorizer (binary)
│
├── knowledge/
│   ├── operators.json             ← NL phrase → SQL operator mappings
│   ├── synonyms.json              ← Word → canonical column name mappings
│   └── stopwords.json             ← Words to remove before processing
│
├── training_data/
│   ├── generate_dataset.py        ← Generates intent_dataset.csv
│   ├── intent_dataset.csv         ← 648 labeled training examples
│   ├── intent_dataset_wikisql.csv ← Additional training data from WikiSQL
│   ├── convert_wikisql.py         ← Converts WikiSQL format to local format
│   └── test.py                    ← Quick training data sanity checks
│
├── data/
│   ├── sample.csv                 ← Demo patient dataset (10 rows)
│   ├── students.csv               ← Demo student dataset (10 rows)
│   └── database.db                ← Auto-generated SQLite database
│
└── tests/
    ├── conftest.py                ← pytest path setup
    ├── test_dataset_and_schema.py ← Tests for loading and schema reading
    ├── test_matchers.py           ← Tests for column + value matching
    ├── test_sql_generation_and_execution.py ← End-to-end SQL tests
    ├── test_tokenizer_and_operator.py       ← Tokenizer + operator tests
    └── test_validator.py          ← SQL validator tests (incl. security)
```

---

## 7. Module Reference

### `main.py`

The entry point. Runs an interactive loop:
1. Asks the user for a CSV file path
2. Loads the dataset and reads the schema
3. Loads the pre-trained ML model **once** (not on every query — this was a bug that has been fixed)
4. Accepts questions in a loop, runs the full pipeline for each, and prints results
5. Supports `change_csv` to switch datasets mid-session, and `exit` to quit

---

### `core/dataset_loader.py`

**Functions:**
- `load_csv(path)` — reads a CSV file into a pandas DataFrame. Tries UTF-8 encoding first; falls back to Latin-1 if the file contains special characters.
- `save_to_sqlite(df, db_path, table_name)` — writes the DataFrame into a SQLite database, replacing any existing table. Automatically creates the `data/` directory if it doesn't exist.
- `load_dataset(csv_path, db_path, table_name)` — combines both steps and returns the DataFrame.

**Why SQLite?** SQLite is built into Python (no installation needed), stores data in a single portable file, and supports full SQL syntax. The database is regenerated from the CSV every time, so there is no stale data.

---

### `core/schema_reader.py`

**Functions:**
- `read_schema(df)` — iterates every column and returns a dictionary with the column's data type and up to **100 unique sample values**. Storing 100 values (instead of just 5 as in the original) dramatically improves categorical value matching on real datasets.
- `get_numeric_columns(schema)` — returns column names whose dtype contains `int` or `float`.
- `get_text_columns(schema)` — returns column names whose dtype is `object`, `str`, `string`, or `category`.

**Example schema output:**
```python
{
    "Age":    {"dtype": "int64",  "sample_values": [45, 32, 28, 55, 61, ...]},
    "Gender": {"dtype": "object", "sample_values": ["Male", "Female"]},
    "District":{"dtype": "object","sample_values": ["Dhaka","Sylhet","Chittagong"]}
}
```

---

### `core/tokenizer.py`

**Functions:**
- `clean_text(text)` — lowercases the text and removes all non-alphanumeric characters (punctuation, symbols).
- `tokenize(text, stopwords_path)` — cleans the text, splits into words, and removes stopwords (common words like "show", "all", "the", "from" that add no meaning for SQL generation).

**Note:** The tokenizer is not used in the main SQL pipeline (the pipeline works on the raw question to preserve positional information needed for operator/value matching). It is used for the intent detection model and is kept as a utility.

---

### `core/intent_detector.py`

**Functions:**
- `load_model(model_path, vectorizer_path)` — loads the pickled Naive Bayes model and TF-IDF vectorizer from disk.
- `predict_intent(text, model, vectorizer)` — transforms the question into a numeric vector and returns the predicted intent string (`SELECT`, `COUNT`, `AVG`, `MAX`, `MIN`, or `SUM`).

---

### `core/operator_detector.py`

**Functions:**
- `load_operators(path)` — loads the phrase-to-symbol mapping from `operators.json`.
- `detect_operators(text, operators_path)` — scans the text for all known operator phrases.

**Algorithm:**
1. Sort phrases longest-first (greedy matching — ensures "greater than or equal to" matches before "greater than")
2. Use `re.finditer` to find **all** occurrences of each phrase (the original code used `str.find()` which only found the first)
3. Track all character positions covered by matched phrases so shorter overlapping phrases are not double-counted
4. Return matches sorted by their position in the sentence

**Output:** `[{"symbol": ">", "position": 15}, {"symbol": "<", "position": 40}]`

---

### `core/attribute_matcher.py`

**Functions:**
- `match_column(word, schema, synonyms_path, threshold)` — attempts to match a single word (or phrase) to a column name:
  1. **Fuzzy direct match** — compares the word to all lowercase column names using `rapidfuzz.fuzz.ratio`. Returns the column if the similarity score meets the threshold (default: 70%).
  2. **Synonym lookup** — if no direct match, checks `synonyms.json`. If the word has a synonym (e.g. "years" → "age"), the synonym is fuzzy-matched against column names.
- `find_columns_in_text(text, schema, synonyms_path)` — tries to match every single word, pair of words (bigram), and triple of words (trigram) in the question. This is what enables multi-word column names like `"First Name"` or `"Date Of Birth"` to be recognized.

---

### `core/value_matcher.py`

**Functions:**
- `extract_numbers(text)` — finds all integers and decimals in the text using `\b\d+(?:\.\d+)?\b`, returned with their character positions.
- `match_categorical_values(text, schema)` — for every text column in the schema, checks if any of its sample values appear in the question (case-insensitive, word-boundary aware). Returns `(column, value)` pairs with the original casing preserved for the SQL query.

**Deduplication:** If the same column matches multiple sample values in one question, only the first match is kept to avoid conflicting filters like `Gender = 'Male' AND Gender = 'Female'`.

---

### `core/sql_generator.py`

**Functions:**
- `build_query(question, schema, intent, ...)` — orchestrates all matching components and builds an internal query dictionary:
  1. Calls `match_categorical_values` → categorical filters
  2. Calls `detect_operators` and `extract_numbers` → numeric filters (including BETWEEN, IS NULL, LIKE)
  3. For aggregate intents (AVG/MAX/MIN/SUM), finds the target column by locating the numeric column word closest to the aggregate keyword in the question
- `query_to_sql(query, table_name)` — converts the internal dictionary to a SQL string. All identifiers are **double-quoted** (e.g. `"Age"`, `"data"`) to correctly handle column names containing spaces or special characters.

**Supported operators in generated SQL:**

| Operator | Example Input | Generated SQL fragment |
|----------|--------------|------------------------|
| `=` | "female patients" | `"Gender" = 'Female'` |
| `>` `<` `>=` `<=` `!=` | "older than 30" | `"Age" > 30` |
| `BETWEEN` | "age between 20 and 40" | `"Age" BETWEEN 20 AND 40` |
| `IS NULL` | "where notes is empty" | `"Notes" IS NULL` |
| `LIKE` | "name contains Ahmed" | `"Name" LIKE '%ahmed%'` |

---

### `core/sql_validator.py`

The validator is a **safety layer** that checks the generated SQL before it is executed. It protects against both errors and misuse.

**Rules checked (in order):**

| Rule | What it checks | Example rejection |
|------|---------------|-------------------|
| 1 | Must start with `SELECT` | `DROP TABLE data;` |
| 2 | No dangerous keywords outside string literals | `DELETE FROM data` |
| 3 | No stacked statements | `SELECT ...; DELETE ...;` |
| 4 | Correct table name after `FROM`/`JOIN` (exact word match, checked on literal-stripped SQL) | `FROM metadata` when table is `data`; `WHERE col = 'from data'` cannot bypass this |
| 5 | All WHERE columns exist in schema | `WHERE "Salary" > 1000` when no Salary column |

**String literal stripping:** Before Rules 2 and 4, all single-quoted string values are replaced with empty placeholders (`''`). This prevents a crafted value like `'drop all data'` from triggering Rule 2, or `'from data'` from fooling Rule 4.

---

### `core/sql_executor.py`

**Functions:**
- `execute_query(sql, db_path)` — opens a SQLite connection, runs the SQL, fetches all rows, and always closes the connection (via `finally` block). Returns `(column_names, rows)`. Handles the edge case where `cursor.description` is `None` (can happen with empty result sets).

---

### `core/response.py`

**Functions:**
- `format_result(column_names, rows)` — builds an aligned ASCII table. Column widths are calculated from the maximum of the header length and the longest data value in each column, so every column is exactly wide enough.
- `print_result(column_names, rows)` — prints the formatted result.

---

## 8. Algorithms & Techniques

### TF-IDF + Naive Bayes (Intent Classification)

**TF-IDF (Term Frequency–Inverse Document Frequency)** converts a text question into a numeric vector where each dimension represents a word or word-pair (bigram). Words that appear frequently in a specific class but rarely overall get high weights.

**Naive Bayes** is a probabilistic classifier based on Bayes' theorem. It assumes all word features are independent (the "naive" assumption) and calculates the probability of each intent class given the word vector. It is chosen for this task because:
- It works well on small training datasets (648 examples)
- Training and prediction are extremely fast
- It is naturally suited for text classification

**Training pipeline:**
```
intent_dataset.csv
       ↓
TF-IDF vectorizer (fit on training text)
       ↓
648 text samples → numeric matrix (bigrams)
       ↓
Naive Bayes classifier (train)
       ↓
Saved: intent_model.pkl + vectorizer.pkl
```

**Prediction:**
```
User question → TF-IDF transform (using saved vectorizer) → numeric vector
       ↓
Naive Bayes predict → "SELECT" / "COUNT" / "AVG" / "MAX" / "MIN" / "SUM"
```

---

### Fuzzy String Matching (Attribute Matching)

**rapidfuzz.fuzz.ratio** computes the similarity between two strings as a percentage (0–100). It uses the **Levenshtein edit distance** — the minimum number of single-character edits (insert, delete, replace) needed to transform one string into the other.

Example:
```
fuzz.ratio("yrs", "age")    → ~33% (no match)
fuzz.ratio("years", "age")  → ~67% (below threshold)
```

But with the synonym lookup: `"years" → "age"` → then `fuzz.ratio("age", "age") = 100%` → match found.

---

### Position-Aware Numeric Filter Assembly

When a question contains multiple numeric filters (e.g. "patients older than 30 with score above 80"), the system needs to match each number to the correct column and operator.

**Algorithm:**
1. Detect all operators with their character positions in the text
2. Detect all numbers with their character positions
3. For each operator (left-to-right), find the first number that appears after it
4. Find the numeric column whose name appears closest (by character distance) to that number
5. Build the filter: `{column, operator, value}`

This position-aware approach correctly assigns "Age > 30" and "Score > 80" independently.

---

### Word-Boundary Regex for Categorical Matching

The pattern `(?<![a-z0-9])female(?![a-z0-9])` ensures "female" is matched as a complete word, preventing "female" from incorrectly matching inside longer strings and preventing "male" from matching inside "female".

---

## 9. Knowledge Files

### `knowledge/operators.json`

Maps natural language phrases to SQL operators. Longer phrases are matched first (greedy) to prevent partial matches.

```json
{
  "greater than or equal to": ">=",
  "greater than": ">",
  "older than": ">",
  "between": "BETWEEN",
  "is null": "IS NULL"
}
```

To add new phrase mappings, simply edit this file — no code changes needed.

---

### `knowledge/synonyms.json`

Maps words a user might say to the canonical concept used in column name matching.

```json
{
  "years": "age",
  "yrs": "age",
  "sex": "gender",
  "wage": "salary",
  "dept": "department",
  "kg": "weight"
}
```

This allows the system to find an "Age" column even if the user says "years old".

---

### `knowledge/stopwords.json`

A list of common English words that carry no meaning for SQL generation and are removed before tokenization:

```json
["show", "list", "all", "the", "a", "of", "find", "tell", "me", "what", ...]
```

---

## 10. Installation Guide

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Steps

**1. Clone or download the project:**
```bash
git clone <repository-url>
cd nl2sql_ai
```

**2. Install all dependencies:**
```bash
pip install -r requirements.txt
```

**`requirements.txt` contents:**
```
pandas
scikit-learn
rapidfuzz
pytest
datasets==2.21.0
```

**3. Verify installation:**
```bash
python -c "import pandas, sklearn, rapidfuzz; print('All dependencies installed.')"
```

The pre-trained model files (`models/intent_model.pkl` and `models/vectorizer.pkl`) are already included. No training is needed to run the system.

---

## 11. Running the Program

```bash
python3 main.py
```

**Interactive prompts:**

```
=== NL to SQL AI (Interactive Mode) ===
CSV file path din (default: data/sample.csv):
```

Press Enter to use the demo dataset, or type a path to your own CSV file.

```
Ekhon joto khushi proshno korte paren.
'exit' likhe ber hoye jaben.
'change_csv' likhe notun CSV file load korte parben.

Apnar proshno:
```

**Available commands:**

| Command | Action |
|---------|--------|
| Any English question | Run NL → SQL pipeline and display result |
| `change_csv` | Load a different CSV file without restarting |
| `exit` / `quit` / `q` | Exit the program |

---

## 12. Dataset Handling

The system is designed to work with **any well-formed CSV file**. No configuration is needed beyond providing the file path.

**What makes a good input CSV:**
- Has a header row (column names in the first row)
- Each column contains one type of data (numbers or text, not mixed)
- Column names are descriptive (the system uses them for matching)

**What the system automatically detects:**
- Number of columns and their names
- Data type of each column (numeric vs. text)
- Up to 100 unique values per column (used for categorical matching)

**Demo datasets included:**

| File | Contents | Rows | Columns |
|------|----------|------|---------|
| `data/sample.csv` | Patient records | 10 | Name, Age, Gender, District, Disease |
| `data/students.csv` | Student records | 10 | Name, Age, Gender, District, GPA, Department |

You can point the system at any CSV file — employee records, product catalogs, sales data, etc.

---

## 13. Model Training

The intent classification model is pre-trained and included. Re-training is only needed if you want to add new intent types or improve accuracy with more training data.

### Training Data Format

`training_data/intent_dataset.csv`:

```csv
question,intent
show all patients,SELECT
how many students,COUNT
average age of patients,AVG
highest salary,MAX
lowest marks,MIN
total income of employees,SUM
```

648 examples across 6 intent classes.

### To Retrain

```bash
# Step 1: (Optional) Regenerate training data
python3 training_data/generate_dataset.py

# Step 2: Train the model
python3 models/train_intent.py
```

Output:
```
Test accuracy: 97.69 %
Model save hoise: models/intent_model.pkl
Vectorizer save hoise: models/vectorizer.pkl
```

### Training Configuration (`models/train_intent.py`)

| Setting | Value | Reason |
|---------|-------|--------|
| Vectorizer | TF-IDF | Converts text to weighted numeric features |
| N-gram range | (1, 2) | Captures single words and word pairs |
| Classifier | Multinomial Naive Bayes | Fast, accurate for short text classification |
| Train/test split | 80% / 20% | Standard ratio for small datasets |
| Random state | 42 | Reproducible results |

---

## 14. Testing

The project includes a comprehensive automated test suite.

### Running Tests

```bash
python -m pytest tests/ -v
```

### Test Coverage

| Test File | What It Tests | Tests |
|-----------|--------------|-------|
| `test_dataset_and_schema.py` | CSV loading, schema column detection, dtype detection | 3 |
| `test_matchers.py` | Direct/synonym column match, number extraction, categorical matching, false-positive prevention | 6 |
| `test_sql_generation_and_execution.py` | SELECT with filters, COUNT, AVG aggregate, end-to-end execution | 4 |
| `test_tokenizer_and_operator.py` | Text cleaning, stopword removal, operator detection | 5 |
| `test_validator.py` | Valid queries pass, dangerous keywords blocked, injection blocked, unknown columns blocked, table name bypass prevention (substring, prefix, string-literal spoof) | 14 |
| **Total** | | **33 tests** |

### Test Design

- Each test uses `tmp_path` (pytest's temporary directory fixture) for the SQLite database, ensuring tests are isolated and don't interfere with each other.
- Tests use the actual knowledge files (`knowledge/operators.json`, `knowledge/synonyms.json`) so they reflect real system behavior.
- Security tests explicitly verify that bypass attempts (e.g. `FROM metadata` spoofing `FROM data`, or `WHERE col = 'from data'`) are correctly rejected.

---

## 15. Example Session

```
=== NL to SQL AI (Interactive Mode) ===
CSV file path din (default: data/sample.csv):

Apnar proshno: show female patients older than 30

Detected intent : SELECT
Internal query  : {'intent': 'SELECT', 'filters': [
    {'column': 'Gender', 'operator': '=', 'value': 'Female'},
    {'column': 'Age', 'operator': '>', 'value': '30'}
], 'agg_column': None}
Generated SQL   : SELECT * FROM "data" WHERE "Gender" = 'Female' AND "Age" > 30

Name   | Age | Gender | District   | Disease
---------------------------------------------
Fatima | 28  | Female | Dhaka      | Asthma
Nusrat | 55  | Female | Chittagong | Diabetes
Sima   | 40  | Female | Sylhet     | Fever
Laila  | 36  | Female | Dhaka      | Diabetes
Rima   | 30  | Female | Chittagong | Fever

--------------------------------------------------

Apnar proshno: how many patients from dhaka

Detected intent : COUNT
Internal query  : {'intent': 'COUNT', 'filters': [
    {'column': 'District', 'operator': '=', 'value': 'Dhaka'}
], 'agg_column': None}
Generated SQL   : SELECT COUNT(*) FROM "data" WHERE "District" = 'Dhaka'

COUNT(*)
--------
3

--------------------------------------------------

Apnar proshno: average age

Detected intent : AVG
Generated SQL   : SELECT AVG("Age") FROM "data"

AVG("Age")
----------
37.7

--------------------------------------------------

Apnar proshno: exit
Bye bye!
```

---

## 16. Limitations

| Limitation | Details |
|------------|---------|
| **OR conditions** | Only `AND` filters are supported. "patients from Dhaka or Sylhet" will not work correctly. |
| **IN operator** | List filtering (e.g. "in Dhaka, Sylhet, Chittagong") is not yet supported. |
| **ORDER BY / LIMIT** | Ranking questions like "top 5 oldest patients" are not yet supported. |
| **JOIN queries** | Only single-table queries are supported. Multi-table JOINs require knowing the relationship between tables. |
| **GROUP BY** | Grouped aggregations like "average age by city" are not yet supported. |
| **Complex nested conditions** | Parenthesized logic like "(age > 30 OR city = 'Dhaka') AND gender = 'Female'" is not supported. |
| **Column name dependency** | The synonym dictionary covers common patterns, but very unusual column names may not be matched without adding entries to `synonyms.json`. |
| **Language** | English only. Multi-language support would require language detection and translation. |
| **Model accuracy** | The intent model is trained on 648 examples. Very unusual phrasings may be misclassified. |

---

## 17. Future Improvements

| Feature | Description |
|---------|-------------|
| **OR / IN support** | Allow "patients from Dhaka or Sylhet" to generate `WHERE "District" IN ('Dhaka', 'Sylhet')` |
| **ORDER BY + LIMIT** | Detect "top N" and "lowest N" patterns to generate `ORDER BY ... DESC LIMIT N` |
| **GROUP BY** | Support "average salary by department" → `GROUP BY "Department"` |
| **Abbreviation expansion** | Split snake_case/camelCase column names (e.g. `emp_dept_nm` → "employee department name") for better matching |
| **Larger training dataset** | Expand intent training data to improve accuracy on rare phrasings |
| **Confidence scores** | Show the model's confidence in its intent prediction and warn when confidence is low |
| **Query history** | Save past questions and results to a session log |
| **Multi-language support** | Detect and translate non-English questions before processing |
| **HAVING clause** | Support filtered aggregations like "departments where average salary > 50000" |
| **Web interface** | An optional browser-based UI for non-technical users (keeping CLI as default) |

---

## Dependencies Summary

```
pandas          — CSV loading, DataFrame operations, SQLite persistence
scikit-learn    — TF-IDF vectorizer, Naive Bayes intent classifier
rapidfuzz       — Fuzzy string matching for column name recognition
pytest          — Automated testing framework
datasets        — WikiSQL training data loading (used during data generation only)
```

All other modules used (`sqlite3`, `re`, `json`, `pickle`, `os`, `sys`) are part of the Python standard library and require no installation.

---

*Project developed as a beginner-to-intermediate demonstration of hybrid AI (machine learning + rule-based) applied to natural language database querying. The system is fully dataset-independent and adapts automatically to any CSV file provided by the user.*
