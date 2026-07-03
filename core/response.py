"""
response.py

Kaj: SQL query theke paoa result-ke shundor, porar-jogyo
table format-e dekhano.
"""


def format_result(column_names, rows):
    """Result-ke ekta readable table-style string banay."""
    if not rows:
        return "Kono result paoa jay nai."

    header = " | ".join(column_names)
    separator = "-" * len(header)

    lines = [header, separator]
    for row in rows:
        lines.append(" | ".join(str(item) for item in row))

    return "\n".join(lines)


def print_result(column_names, rows):
    """format_result() diye result print kore."""
    print(format_result(column_names, rows))
