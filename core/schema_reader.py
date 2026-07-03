"""
schema_reader.py

Kaj: DataFrame theke schema ber kora — kon kon column ache,
protar data type ki, ebong sample value.

Bug fixes:
- sample_values: 5 theke 100-e barano hoise. Matro 5 ta value
  rakha hole categorical matching ektai choto dataset-e kono value
  detect korte parbe na. 100 ta unique value rakhle matching accurate hobe.
- is_categorical / is_numeric flag add kora hoise jate onno module gula
  easily dtype check korte pare.
"""

# Akta column-er janya koto ta unique value sample hisebe rakhbo.
# Beshi hole memory badhbe, kome gele categorical matching miss korbe.
MAX_SAMPLE_VALUES = 100


def read_schema(df):
    """
    DataFrame theke schema dictionary banay.

    Format:
    {
        "Age":    {"dtype": "int64",   "sample_values": [45, 30, 52, ...]},
        "Gender": {"dtype": "object",  "sample_values": ["Male", "Female"]},
        "Score":  {"dtype": "float64", "sample_values": [8.5, 9.0, 7.2, ...]}
    }

    sample_values-e akta column-er shob unique value (up to MAX_SAMPLE_VALUES)
    rakha hoy, jate value_matcher categorical value gula sothik-bhabe
    detect korte pare.
    """
    schema = {}

    for column in df.columns:
        # NaN bad diye unique value ber kora
        unique_values = df[column].dropna().unique()

        # Shob unique value rakhbo, tobe MAX_SAMPLE_VALUES-er beshi noy
        sample_values = unique_values[:MAX_SAMPLE_VALUES].tolist()

        schema[column] = {
            "dtype": str(df[column].dtype),
            "sample_values": sample_values,
        }

    return schema


def get_column_names(df):
    """Sudhu column name gular list return kore."""
    return list(df.columns)


def is_numeric_dtype(dtype_str):
    """Akta dtype string numeric (int/float) kina check kore."""
    return "int" in dtype_str or "float" in dtype_str


def is_text_dtype(dtype_str):
    """Akta dtype string text/categorical kina check kore."""
    return dtype_str in ("object", "str", "string", "category")


def get_numeric_columns(schema):
    """Schema theke shudhu numeric (int/float) column gula ber kore."""
    return [col for col, info in schema.items() if is_numeric_dtype(info["dtype"])]


def get_text_columns(schema):
    """Schema theke shudhu text (object/string/category) column gula ber kore."""
    return [col for col, info in schema.items() if is_text_dtype(info["dtype"])]


def print_schema(schema):
    """Schema ta terminal e sundor kore print kore (debug er jonno)."""
    for column, info in schema.items():
        print("Column:", column)
        print("  Type:", info["dtype"])
        print("  Samples:", info["sample_values"][:10])  # printe matro 10 ta dekhano


# Quick test
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from dataset_loader import load_dataset

    df = load_dataset("../data/sample.csv", "../data/database.db")
    schema = read_schema(df)
    print_schema(schema)
