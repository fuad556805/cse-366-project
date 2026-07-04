---
name: nl2sql multi-word column phrase matching
description: How multi-word column names (e.g. "Purchase Amount ($)") are matched in questions, and why dangerous fallbacks were removed
---

## Rule
`core/attribute_matcher.py`'s `find_columns_with_positions()` does stopword-aware sliding-window phrase matching: it strips stopwords from both the question tokens and each column's normalized core words, then slides a window sized to each column's core-word-count across the question tokens, fuzzy-comparing the whole phrase (not word-by-word). A secondary whole-text `token_set_ratio` fallback pass catches partial mentions (e.g. "review" -> "Review Score").

`_normalize()`/`_strip_symbols()` also strips bracket contents and symbols so "Purchase Amount ($)" / "Time Spent on Website (min)" normalize to clean phrases before matching.

`core/sql_generator.py` consumes this via a single `column_matches = find_columns_with_positions(...)` call per `build_query()`, then picks the nearest match by character position for aggregates/order-by/group-by/filters — instead of the old approach of matching each word individually, which failed on multi-word columns and could accidentally match the wrong numeric column.

**Why:** Per-word matching couldn't detect multi-word column names, so aggregate queries like "average time spent on the website" silently fell back to the first/nearest numeric column (e.g. "Customer ID") producing wrong-but-plausible-looking SQL. The `numeric_columns[0]` fallback in `_find_agg_column`/`_detect_order_limit` was removed entirely — when no column can be resolved, `query_to_sql()` now raises `ValueError` (caught in `app.py`/`main.py` and shown as a user-facing message) rather than guessing.

**How to apply:** When adding new column-matching logic in this project, always operate on `find_columns_with_positions()` results (phrase + position) rather than looping over individual words with `match_column()`. Never silently default an aggregate/order column to "the first numeric column" — raise/return `None` and surface a clear error instead.
