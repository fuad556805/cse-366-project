---
name: nl2sql project constraints
description: Hard rules for the nl2sql_ai project — what must never change
---

## Rules
- Output must be **pure Python CLI only** — no web UI, HTML, CSS, JS, Flask, FastAPI, Streamlit, Django, React
- Existing project structure and file names must not change (no renames, no new top-level modules)
- Code must be **dataset-independent** — no hardcoded column names (Age, Gender, GPA, Salary, etc.)
- Bengali (Bangla) comments in the source files are intentional project style — preserve them
- `data/sample.csv` and `data/students.csv` must exist for tests; they were missing on import and were created

**Why:** User explicitly stated these constraints in the task brief. Violating any of them is a blocking issue.
