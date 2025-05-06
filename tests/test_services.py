import pandas as pd
import pytest

from src.services import analyze_cashback_categories


def test_analyze_cashback_no_transactions():
    data = {
        "Дата операции": [
            "2023-10-01 12:00:00",
            "2023-10-02 14:30:00"
        ],
        "Категория": [
            "Food",
            "Transport"
        ],
        "Сумма платежа": [
            200.0,
            100.0
        ]
    }

    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    year = 2023
    month = 9

    expected_result = {}

    result = analyze_cashback_categories(df, year, month)

    assert result == expected_result, f"Ожидается {expected_result}, получено {result}"


def test_analyze_cashback_empty_dataframe():
    df = pd.DataFrame(columns=["Дата операции", "Категория", "Сумма платежа"])

    year = 2023
    month = 9

    expected_result = {}

    result = analyze_cashback_categories(df, year, month)

    assert result == expected_result, f"Ожидается {expected_result}, получено {result}"
