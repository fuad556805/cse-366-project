"""
response.py

Kaj: SQL query theke paoa result-ke shundor, porar-jogyo
table format-e dekhano.

Improvement:
- Separator width ekhon protiṭi column-er actual max content width
  onujayi calculate hoy — agey shudhu header-er length use hoto,
  ekhon data row gula-o consider kore.
"""


def format_result(column_names, rows):
    """
    Result-ke ekta readable table-style string banay.

    Empty result hole "Kono result paoa jay nai." return kore.
    """
    if not rows:
        return "Kono result paoa jay nai."

    # Protyek column-er max width: header ba data je baro seta
    col_widths = []
    for i, col in enumerate(column_names):
        max_data_width = max(
            (len(str(row[i])) for row in rows),
            default=0,
        )
        col_widths.append(max(len(col), max_data_width))

    def fmt_row(values):
        return " | ".join(
            str(v).ljust(col_widths[i]) for i, v in enumerate(values)
        )

    header = fmt_row(column_names)
    separator = "-" * len(header)

    lines = [header, separator]
    for row in rows:
        lines.append(fmt_row(row))

    return "\n".join(lines)


def print_result(column_names, rows):
    """format_result() diye result print kore."""
    print(format_result(column_names, rows))
