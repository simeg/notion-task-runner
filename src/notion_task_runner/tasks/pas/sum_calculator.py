from typing import Any


class SumCalculator:
    """
    Calculates the total sum of "Slutpris" values from a list of Notion-style row dictionaries.

    This class processes a list of dictionaries representing database rows, each containing nested property data.
    It extracts the "Slutpris" field (if present and numeric) and returns the summed total as an integer.
    """

    def calculate(self, rows: list[dict[str, Any]]) -> float:
        total = 0
        for item in rows:
            slutpris = item["properties"].get("Slutpris", {}).get("number")
            if slutpris is not None:
                total += slutpris
        return int(total)
