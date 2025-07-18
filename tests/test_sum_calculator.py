from notion_task_runner.tasks.pas.sum_calculator import SumCalculator

def test_calculate_handles_valid_and_missing_data(calculator: SumCalculator):
    rows = [
        {"properties": {"Slutpris": {"number": 10}}},
        {"properties": {"Slutpris": {"number": 20}}},
        {"properties": {"Slutpris": {"number": None}}},
        {"properties": {"Slutpris": {}}},
        {"properties": {}},
    ]

    assert calculator.calculate_total_for_column(rows, "Slutpris") == 30

def test_calculate_returns_exact_integer(calculator: SumCalculator):
    rows = [
        {"properties": {"Slutpris": {"number": 10}}},
        {"properties": {"Slutpris": {"number": 20}}},
    ]

    result = calculator.calculate_total_for_column(rows, "Slutpris")

    assert result == 30, "Value should be 30"
    assert type(result) is int, f"Expected int but got {type(result).__name__}"

def test_calculate_with_empty_list(calculator: SumCalculator):
    assert calculator.calculate_total_for_column([]) == 0

def test_calculate_with_only_invalid_data(calculator: SumCalculator):
    rows = [
        {"properties": {}},
        {"properties": {"Slutpris": {}}},
        {"properties": {"Slutpris": {"number": None}}},
    ]
    assert calculator.calculate_total_for_column(rows, "Slutpris") == 0

def test_calculate_with_negative_values(calculator: SumCalculator):
    rows = [
        {"properties": {"Slutpris": {"number": -10}}},
        {"properties": {"Slutpris": {"number": 20}}},
    ]
    assert calculator.calculate_total_for_column(rows, "Slutpris") == 10

def test_calculate_with_float_values(calculator: SumCalculator):
    rows = [
        {"properties": {"Slutpris": {"number": 10.5}}},
        {"properties": {"Slutpris": {"number": 19.5}}},
    ]
    assert calculator.calculate_total_for_column(rows, "Slutpris") == 30
    assert type(calculator.calculate_total_for_column(rows, "Slutpris")) is int

def test_calculate_with_large_values(calculator: SumCalculator):
    rows = [
        {"properties": {"Slutpris": {"number": 10_000_000}}},
        {"properties": {"Slutpris": {"number": 20_000_000}}},
    ]
    assert calculator.calculate_total_for_column(rows, "Slutpris") == 30_000_000