# nl2sql_ai

Natural Language theke SQL query generate kora - AI (Intent Detection) +
Rule-based (Operator/Attribute/Value Matching) hybrid system.

## Kivabe Chalabe

```bash
pip install -r requirements.txt

# Model already train kora ache (models/intent_model.pkl).
# Notun kore train korte chaile:
python3 training_data/generate_dataset.py
python3 models/train_intent.py

# Pipeline chalate:
python3 main.py
```

Tarpor CSV file path ebong English-e ekta question dite hobe. Jemon:

```
CSV file path din (default: data/sample.csv): data/sample.csv
Apnar proshno din: show female patients older than 30
```

## Pipeline (Architecture)

```
CSV Upload
   |
Schema Read (dataset_loader.py, schema_reader.py)
   |
Intent Detection - ML (intent_detector.py, models/)
   |
Operator Detection - Rule-based (operator_detector.py)
   |
Attribute Matching - Schema Matching (attribute_matcher.py)
   |
Value Matching - Schema Values (value_matcher.py)
   |
SQL Generator (sql_generator.py)
   |
SQL Validator - safety + column check (sql_validator.py)
   |
SQL Executor (sql_executor.py)
   |
Result (response.py)
```

## Folder Structure

```
nl2sql_ai/
├── main.py                    - shob module jure pipeline chalay
├── requirements.txt
├── data/
│   ├── sample.csv              - patient dataset (demo)
│   ├── students.csv            - student dataset (multi-dataset test)
│   └── database.db             - auto generate hoy (CSV theke)
├── models/
│   ├── train_intent.py         - intent classification model train kore
│   ├── intent_model.pkl        - trained model
│   └── vectorizer.pkl          - TF-IDF vectorizer
├── core/
│   ├── dataset_loader.py       - CSV load + SQLite e save
│   ├── schema_reader.py        - column, dtype, sample value ber kore
│   ├── tokenizer.py            - question ke token e bhage
│   ├── intent_detector.py      - ML diye intent predict kore
│   ├── operator_detector.py    - "greater than" -> ">" ei rokom detect kore
│   ├── attribute_matcher.py    - column name fuzzy match kore
│   ├── value_matcher.py        - number ebong categorical value ber kore
│   ├── sql_generator.py        - internal query -> SQL string
│   ├── sql_validator.py        - execute korar age SQL safety+correctness check
│   ├── sql_executor.py         - SQLite e SQL run kore
│   └── response.py             - result table format e dekhay
├── knowledge/
│   ├── operators.json          - "older than" -> ">" mapping
│   ├── synonyms.json           - "years" -> "age" mapping
│   └── stopwords.json          - "show", "all", "the" etc.
├── training_data/
│   ├── generate_dataset.py     - intent training data toiri kore
│   └── intent_dataset.csv      - 648 example (6 intent)
└── tests/                      - pytest suite (18 tests)
```

## Intent Categories

`SELECT`, `COUNT`, `AVG`, `MAX`, `MIN`, `SUM`

## Multi-Dataset Support

Column name jekono kichu hote pare (Age/Years, Gender/Sex, District/City) -
`synonyms.json` + fuzzy matching diye system nijei bujhe nay kon column
ki mane bahon kore. `data/sample.csv` (patient data) ebong
`data/students.csv` (student data) - dutar upor-i test kora hoise.

## Test Chalate

```bash
python3 -m pytest tests/ -v
```

## Limitation (Beginner Project - Janar Jonno)

- Column-er naam question-e directly ba synonym hisebe thaka lage
  (jemon "older" -> synonym theke "age"). Ekdom notun/ochena word hole
  match nao hote pare.
- Complex nested condition (jemon "OR" logic, ba "between X and Y")
  currently support kora hoy na - shudhu "AND" style filter chain hoy.
