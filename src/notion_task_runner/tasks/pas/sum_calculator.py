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
    ) -> float:
        def extract_number(item: dict[str, Any]) -> Any:
            return item["properties"].get(column_name, {}).get("number")

        numbers = map(extract_number, rows)
        filtered_numbers = filter(lambda x: x is not None, numbers)
        return int(sum(filtered_numbers))
