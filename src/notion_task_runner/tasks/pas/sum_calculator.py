from typing import Any


class SumCalculator:
    """
    Calculates the total sum of values of column name from a list of Notion-style row dictionaries.

    This class processes a list of dictionaries representing database rows, each containing nested property data.
    It extracts the "column_name" field (if present and numeric) and returns the summed total as an integer.
    """

    @staticmethod
    def calculate_total_for_column(
        rows: list[dict[str, Any]], column_name: str
    ) -> int:
        total = 0
        for item in rows:
            price = item["properties"].get(column_name, {}).get("number")
            if price is not None:
                total += price
        return int(total)
