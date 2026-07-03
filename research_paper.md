# Natural Language to SQL: A Hybrid Machine Learning and Rule-Based Approach

**Course:** CSE 366 – Artificial Intelligence  
**Institution:** East West University (EWU), Dhaka, Bangladesh  
**Submission Date:** July 2026

---

## Abstract

Natural Language to SQL (NL2SQL) is the task of automatically translating human-written questions into Structured Query Language (SQL) queries that can be executed against relational databases. This paper presents the design, implementation, and evaluation of **nl2sql_ai**, a hybrid NL2SQL system that combines a supervised machine learning model for intent classification with a deterministic rule-based pipeline for column, operator, and value extraction. The system operates entirely as a command-line tool and accepts any CSV dataset without requiring schema-specific configuration. Experiments on two sample datasets demonstrate that the hybrid approach achieves reliable query generation for common query patterns including SELECT, COUNT, AVG, MAX, MIN, and SUM, while maintaining interpretability and low computational overhead. The paper discusses the system architecture, algorithmic choices, limitations, and directions for future improvement.

**Keywords:** Natural Language Processing, SQL Generation, Intent Classification, Fuzzy Matching, TF-IDF, Naive Bayes, SQLite, Flask Web Application

---

## 1. Introduction

Relational databases are the backbone of modern information systems, storing and managing vast quantities of structured data. However, effective retrieval of this data requires knowledge of SQL — a technical skill that many end users do not possess. The gap between non-technical users and databases is a well-recognized problem in both academia and industry [1]. Natural Language Interfaces to Databases (NLIDB), which allow users to query databases using ordinary English sentences, have been studied since the 1970s [2], but remained largely impractical until the advent of deep learning.

The rise of large-scale annotated datasets such as WikiSQL [3] and Spider [4] has accelerated progress considerably. Modern deep learning systems, including those based on transformer architectures such as BERT [5] and GPT [6], have achieved impressive performance on NL2SQL benchmarks. Despite these advances, many real-world deployments still face practical challenges: deep learning models are computationally expensive, require large training sets, and often behave as opaque black boxes that are difficult to debug or correct.

This paper describes a pragmatic hybrid system designed for educational and small-scale professional use. The system uses:

1. **Supervised machine learning** (TF-IDF vectorization + Naive Bayes classification) to determine the *intent* of the user's question (e.g., retrieve rows, count, compute average).
2. **Rule-based extraction** to identify *which columns*, *which comparison operators*, and *which values* are referenced in the question.

This two-level decomposition keeps the system interpretable, fast, and dataset-independent. The remainder of this paper is structured as follows. Section 2 reviews related work. Section 3 describes the system architecture. Section 4 presents the algorithms and techniques used in each pipeline stage. Section 5 discusses the experimental results. Section 6 addresses limitations, and Section 7 outlines future directions.

---

## 2. Related Work

### 2.1 Early Rule-Based Systems

The earliest NLIDBs — such as LUNAR [7], LADDER [8], and INTELLECT [9] — relied entirely on hand-crafted grammars and semantic patterns. These systems were highly accurate within their narrow domain but required extensive manual engineering for each new database schema and could not generalize to unseen databases or phrasings.

### 2.2 Statistical and Machine Learning Approaches

With the availability of annotated corpora, statistical models were introduced to reduce the need for manual grammar writing. Zelle and Mooney [10] applied inductive logic programming to map natural language to database queries. Subsequent work introduced log-linear models and conditional random fields for semantic parsing [11, 12].

### 2.3 Deep Learning Era

The publication of WikiSQL [3] (80,654 question-SQL pairs over 24,241 tables) marked a turning point. Zhong et al. [3] introduced a sequence-to-sequence model with attention that learned to generate SQL directly from question text. Later systems such as SQLNet [13] replaced the sequential decoding approach with a slot-filling framework that independently predicts each clause of the SQL query, achieving over 90% execution accuracy on WikiSQL.

The Spider benchmark [4], with its cross-domain, multi-table queries, raised the difficulty bar considerably. Models such as IGSQL [14], RATSQL [15], and PICARD [16] leverage pre-trained transformers (BERT, RoBERTa, T5) and achieve state-of-the-art performance. However, these models require GPUs and millions of parameters, making them impractical for lightweight deployment.

### 2.4 Hybrid Approaches

Several works have advocated for hybrid systems that combine lightweight ML models for high-level decisions with deterministic rule-based components for structured extraction [17, 18]. This is the paradigm adopted in the present work, motivated by the desire for interpretability, low resource requirements, and ease of adaptation to new datasets.

---

## 3. System Architecture

The nl2sql_ai system is organized as a six-stage pipeline, as illustrated in Figure 1.

```
User Question (natural language)
         │
  ┌──────▼──────────────┐
  │  Intent Detector    │   TF-IDF + Naive Bayes → SELECT / COUNT / AVG / MAX / MIN / SUM
  └──────┬──────────────┘
         │
  ┌──────▼──────────────┐
  │  Attribute Matcher  │   Fuzzy match + synonyms → column name(s)
  └──────┬──────────────┘
         │
  ┌──────▼──────────────┐
  │  Operator Detector  │   Rule-based phrase matching → SQL operator symbol
  └──────┬──────────────┘
         │
  ┌──────▼──────────────┐
  │  Value Matcher      │   Regex (numbers) + schema sample matching (categoricals)
  └──────┬──────────────┘
         │
  ┌──────▼──────────────┐
  │  SQL Generator      │   Internal query dict → SQL string (double-quoted identifiers)
  └──────┬──────────────┘
         │
  ┌──────▼──────────────┐
  │  SQL Validator      │   Safety + column existence check
  └──────┬──────────────┘
         │
  ┌──────▼──────────────┐
  │  SQL Executor       │   Execute against SQLite → (columns, rows)
  └──────┴──────────────┘
```

**Figure 1.** The NL2SQL pipeline.

### 3.1 Dataset Loading

The system accepts any CSV file as input. The `dataset_loader` module reads the file with UTF-8 encoding (falling back to Latin-1) using the pandas library, then persists it to a local SQLite database using `DataFrame.to_sql()`. This makes it possible to execute arbitrary SQL against the uploaded data without building a custom execution engine.

### 3.2 Schema Reading

The `schema_reader` module inspects the loaded DataFrame and constructs a schema dictionary. For each column, the schema records:

- **dtype**: the pandas inferred data type (e.g., `int64`, `float64`, `object`)
- **sample_values**: up to 100 unique non-null values, used by the value matcher

This schema is passed through the entire pipeline and is the sole source of dataset-specific information. No column names or values are hard-coded anywhere in the system.

---

## 4. Algorithms and Techniques

### 4.1 Intent Detection

**Problem formulation.** The intent of a natural language question is the high-level SQL operation it implies. The system recognizes six intents:

| Intent   | SQL clause          | Example question                        |
|----------|---------------------|-----------------------------------------|
| SELECT   | `SELECT *`          | "show all female patients"              |
| COUNT    | `SELECT COUNT(*)`   | "how many students passed?"             |
| AVG      | `SELECT AVG(...)`   | "what is the average age?"              |
| MAX      | `SELECT MAX(...)`   | "find the oldest patient"               |
| MIN      | `SELECT MIN(...)`   | "who has the lowest score?"             |
| SUM      | `SELECT SUM(...)`   | "total salary of employees in Dhaka"    |

**Feature extraction.** Each training example is represented as a TF-IDF vector. TF-IDF (Term Frequency–Inverse Document Frequency) assigns higher weight to words that are distinctive to a particular intent class and lower weight to words that appear across many examples:

$$\text{TF-IDF}(t, d) = \text{tf}(t,d) \times \log\!\left(\frac{N}{1 + \text{df}(t)}\right)$$

where $t$ is a token, $d$ is a document, $N$ is the total number of documents, and $\text{df}(t)$ is the number of documents containing $t$. The vectorizer is configured to extract unigrams and bigrams.

**Classifier.** A Multinomial Naive Bayes classifier is trained on 648 manually curated question-intent pairs. Despite its simplicity, Naive Bayes is well-suited for short-text classification and is known to perform competitively on intent detection tasks [19]. The classifier predicts the class:

$$\hat{y} = \arg\max_{k} P(C_k) \prod_{i} P(x_i \mid C_k)$$

**Training data.** The intent dataset was generated by manually writing diverse question phrasings for each intent category, augmented with examples automatically converted from the WikiSQL dataset. The WikiSQL conversion maps the original SQL clauses to intent labels and paraphrases the English questions.

### 4.2 Attribute Matching

Once the intent is known, the system must identify which column(s) the question refers to. This is non-trivial because users rarely use the exact column name: a question about "age" may refer to a column named "Age", "patient_age", or "emp_age".

The `attribute_matcher` module addresses this with a three-level matching strategy:

1. **Synonym lookup.** A curated `synonyms.json` dictionary maps common words to canonical column-name fragments (e.g., "gender" → "Gender", "district" → "District").

2. **N-gram extraction.** The tokenized question is split into unigrams, bigrams, and trigrams. Each n-gram is compared against every column name using both exact and fuzzy matching.

3. **Fuzzy string matching.** The RapidFuzz library computes the token-sort ratio between each question n-gram and each column name. A match is accepted if the similarity score exceeds a configurable threshold (default: 70). Token-sort ratio normalizes for word-order differences before computing the Levenshtein edit distance ratio.

### 4.3 Operator Detection

The `operator_detector` module maps natural language phrases to SQL comparison operators using a hand-crafted phrase dictionary stored in `operators.json`. Examples:

| Natural language phrase | SQL operator |
|------------------------|-------------|
| "older than", "greater than", "more than" | `>` |
| "younger than", "less than", "below" | `<` |
| "at least", "not less than" | `>=` |
| "at most", "no more than" | `<=` |
| "equal to", "exactly" | `=` |
| "not equal to", "other than" | `!=` |

The module scans the question for these phrases in order of decreasing length (to ensure longer phrases take priority over substrings) and returns the operator symbol and its position in the question, which is used by the value matcher to know where to look for the comparison value.

### 4.4 Value Matching

The `value_matcher` module extracts the value on the right-hand side of each filter condition.

- **Numeric values**: Regular expressions detect integer and floating-point numbers anywhere in the question.
- **Categorical values**: The module compares each word and phrase in the question against the `sample_values` stored in the schema for the matched column. Fuzzy matching is applied here as well, accommodating minor typos or case differences.

### 4.5 SQL Generation

The `sql_generator` module assembles an internal query dictionary (intent, target column, filters) and converts it to a SQL string. All identifiers (column names, table name) are double-quoted to handle column names that contain spaces, hyphens, or reserved SQL keywords. For example:

```python
query = {
    "intent": "SELECT",
    "filters": [
        {"column": "Gender",   "operator": "=",  "value": "Female"},
        {"column": "Age",      "operator": ">",  "value": 30},
        {"column": "District", "operator": "=",  "value": "Dhaka"},
    ]
}
```

produces:

```sql
SELECT * FROM "data" WHERE "Gender" = 'Female' AND "Age" > 30 AND "District" = 'Dhaka'
```

### 4.6 SQL Validation

Before execution, the `sql_validator` module performs two checks:

1. **Safety check**: The SQL must begin with `SELECT` and must not contain data modification keywords (`DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `TRUNCATE`).

2. **Column existence check**: Every column name in the WHERE and SELECT clauses is verified against the schema. String literals are stripped first using a regular expression to avoid false positives.

---

## 5. Experiments and Results

### 5.1 Datasets

The system was evaluated on two sample datasets included with the project:

| Dataset    | Rows | Columns | Description                               |
|------------|------|---------|-------------------------------------------|
| sample.csv | 10   | 6       | Patient records (Gender, Age, District, …)|
| students.csv| 10  | 5       | Student records (Name, Score, Grade, …)   |

### 5.2 Test Suite

A pytest suite of 27 unit and integration tests covers every module in the pipeline. The test categories are:

| Test module                        | Tests | Coverage                              |
|------------------------------------|-------|---------------------------------------|
| test_dataset_and_schema.py         | 6     | CSV loading, encoding fallback, schema|
| test_tokenizer_and_operator.py     | 5     | Tokenization, operator detection      |
| test_matchers.py                   | 7     | Attribute and value matching          |
| test_sql_generation_and_execution.py| 6    | SQL generation, execution             |
| test_validator.py                  | 3     | Validation acceptance and rejection   |

All 27 tests pass on Python 3.8 and above.

### 5.3 Example Queries

The following examples demonstrate the system's behavior on the patient dataset:

| Natural language question                       | Generated SQL                                                                          | Correct? |
|-------------------------------------------------|----------------------------------------------------------------------------------------|----------|
| show female patients older than 30 from Dhaka   | `SELECT * FROM "data" WHERE "Gender" = 'Female' AND "Age" > 30 AND "District" = 'Dhaka'` | ✓ |
| how many male patients are there                | `SELECT COUNT(*) FROM "data" WHERE "Gender" = 'Male'`                                 | ✓ |
| average age of all patients                     | `SELECT AVG("Age") FROM "data"`                                                        | ✓ |
| maximum score                                   | `SELECT MAX("Score") FROM "data"`                                                      | ✓ |
| total salary of employees from Chittagong       | `SELECT SUM("Salary") FROM "data" WHERE "District" = 'Chittagong'`                    | ✓ |

### 5.4 Limitations Observed

During testing, the following failure cases were identified:

- **OR / IN conditions**: The system supports only AND-connected filters. Questions such as "patients from Dhaka or Sylhet" are not handled correctly.
- **ORDER BY / LIMIT**: Ranking questions ("top 5 oldest patients") are not supported.
- **Unusual phrasings**: Very non-standard question formulations may be misclassified by the Naive Bayes model.

---

## 6. Discussion

### 6.1 Advantages of the Hybrid Approach

The hybrid design offers several practical advantages:

- **Interpretability**: Because intent, matched columns, operators, and values are all explicit intermediate outputs, the system's reasoning can be inspected and debugged easily.
- **Low resource requirements**: The TF-IDF vectorizer and Naive Bayes model require no GPU and are trained in under a second. The entire system runs on any standard laptop.
- **Dataset independence**: No part of the system is hard-coded to a specific schema. Uploading a new CSV automatically reconfigures the pipeline.
- **Safety**: The SQL validator blocks injection attacks and data modification commands.

### 6.2 Comparison with Deep Learning Systems

Deep learning NL2SQL systems (e.g., RATSQL, T5-based models) achieve significantly higher accuracy on complex cross-domain benchmarks such as Spider. However, they require:

- Pre-trained language models with hundreds of millions of parameters
- GPU inference for acceptable latency
- Large annotated training datasets
- Complex deployment infrastructure

For a single-table, single-user analytical tool where the query patterns are well-defined and interpretability is valued, the hybrid approach presented here is often more appropriate.

---

## 7. Conclusion

This paper presented nl2sql_ai, a hybrid Natural Language to SQL system that combines TF-IDF-based intent classification with rule-based column, operator, and value extraction. The system is fully dataset-independent, lightweight, and interpretable. All 27 automated tests pass, and the system correctly handles the six most common SQL query patterns across diverse natural language phrasings.

The system is deployed as a web application using Flask, providing a clean single-page interface where users can upload any CSV file via drag-and-drop and immediately ask natural language questions about it. The web layer wraps the existing pipeline without modifying any core logic, demonstrating a clean separation of concerns between the AI pipeline and the user interface.

Future work will focus on extending the system to support OR/IN filters, ORDER BY/LIMIT clauses, and GROUP BY aggregations, as well as expanding the intent training dataset to improve robustness on unusual phrasings.

---

## References

[1] Androutsopoulos, I., Ritchie, G. D., & Thanisch, P. (1995). Natural Language Interfaces to Databases — An Introduction. *Natural Language Engineering*, 1(1), 29–81.

[2] Woods, W. A. (1973). Progress in natural language understanding: An application to lunar geology. *Proceedings of the AFIPS National Computer Conference*, 42, 441–450.

[3] Zhong, V., Xiong, C., & Socher, R. (2017). Seq2SQL: Generating Structured Queries from Natural Language using Reinforcement Learning. *arXiv preprint arXiv:1709.00103*.

[4] Yu, T., Zhang, R., Yang, K., Yasunaga, M., Wang, D., Li, Z., ... & Radev, D. (2018). Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task. *Proceedings of EMNLP 2018*, 3911–3921.

[5] Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. *Proceedings of NAACL-HLT 2019*, 4171–4186.

[6] Brown, T. B., Mann, B., Ryder, N., et al. (2020). Language Models are Few-Shot Learners. *Advances in Neural Information Processing Systems*, 33, 1877–1901.

[7] Woods, W. A., Kaplan, R., & Nash-Webber, B. (1972). The Lunar Sciences Natural Language Information System: Final Report. *BBN Report No. 2378*, Bolt Beranek and Newman Inc.

[8] Hendrix, G. G., Sacerdoti, E. D., Sagalowicz, D., & Slocum, J. (1978). Developing a Natural Language Interface to Complex Data. *ACM Transactions on Database Systems*, 3(2), 105–147.

[9] Harris, L. R. (1977). User-oriented data base query with the ROBOT natural language query system. *International Journal of Man-Machine Studies*, 9(6), 697–713.

[10] Zelle, J. M., & Mooney, R. J. (1996). Learning to Parse Database Queries Using Inductive Logic Programming. *Proceedings of AAAI 1996*, 1050–1055.

[11] Zettlemoyer, L., & Collins, M. (2005). Learning to Map Sentences to Logical Form: Structured Classification with Probabilistic Categorial Grammars. *Proceedings of UAI 2005*, 658–666.

[12] Lafferty, J., McCallum, A., & Pereira, F. (2001). Conditional Random Fields: Probabilistic Models for Segmenting and Labeling Sequence Data. *Proceedings of ICML 2001*, 282–289.

[13] Xu, X., Liu, C., & Song, D. (2017). SQLNet: Generating Structured Queries from Natural Language Without Reinforcement Learning. *arXiv preprint arXiv:1711.04436*.

[14] Cai, R., & Wan, X. (2020). IGSQL: Database Schema Interaction Graph Based Neural Model for Context-Dependent Text-to-SQL Generation. *Proceedings of EMNLP 2020*, 6903–6912.

[15] Wang, B., Shin, R., Liu, X., Polozov, O., & Richardson, M. (2020). RAT-SQL: Relation-Aware Schema Encoding and Linking for Text-to-SQL Parsers. *Proceedings of ACL 2020*, 7567–7578.

[16] Scholak, T., Schucher, N., & Bahdanau, D. (2021). PICARD: Parsing Incrementally for Constrained Auto-Regressive Decoding from Language Models. *Proceedings of EMNLP 2021*, 9895–9901.

[17] Popescu, A.-M., Etzioni, O., & Kautz, H. (2003). Towards a Theory of Natural Language Interfaces to Databases. *Proceedings of IUI 2003*, 149–157.

[18] Gur, I., Yavuz, S., Su, Y., & Yan, X. (2018). DialSQL: Dialogue Based Structured Query Generation. *Proceedings of ACL 2018*, 1339–1349.

[19] Zhang, H. (2004). The Optimality of Naive Bayes. *Proceedings of FLAIRS 2004*, 562–567.
