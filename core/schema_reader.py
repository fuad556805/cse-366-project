"""
schema_reader.py

Kaj: DataFrame theke schema ber kora - mane kon kon column ache,
protar data type ki, ebong kichu sample value.

Eta porer step (attribute_matcher, value_matcher) e kaje lagbe,
karon amra jani na user kon dataset upload korbe.
"""


def read_schema(df):
    """
    DataFrame theke schema dictionary banay.
    Format:
    {
        "Age": {"dtype": "int64", "sample_values": [45, 30, 52]},
        "Gender": {"dtype": "object", "sample_values": ["Male", "Female"]}
    }
    """
    schema = {}

    for column in df.columns:
        column_data = df[column].dropna().unique()
        sample_values = column_data[:5].tolist()

        schema[column] = {
            "dtype": str(df[column].dtype),
            "sample_values": sample_values
        }

    return schema


def get_column_names(df):
    """Sudhu column name gular list return kore."""
    return list(df.columns)


def get_numeric_columns(schema):
    """Schema theke shudhu numeric (int/float) column gula ber kore."""
    numeric_columns = []
    for column, info in schema.items():
        if "int" in info["dtype"] or "float" in info["dtype"]:
            numeric_columns.append(column)
    return numeric_columns


def get_text_columns(schema):
    """Schema theke shudhu text (object/string) column gula ber kore."""
    text_columns = []
    for column, info in schema.items():
        # pandas version bhede text column er dtype "object" ba "str"
        # dutai hote pare, tai duitai check korchi.
        if info["dtype"] in ("object", "str"):
            text_columns.append(column)
    return text_columns


def print_schema(schema):
    """Schema ta terminal e sundor kore print kore (debug er jonno)."""
    for column, info in schema.items():
        print("Column:", column)
        print("  Type:", info["dtype"])
        print("  Samples:", info["sample_values"])


# Quick test
if __name__ == "__main__":
    from dataset_loader import load_dataset

    df = load_dataset("../data/sample.csv", "../data/database.db")
    schema = read_schema(df)
    print_schema(schema)
