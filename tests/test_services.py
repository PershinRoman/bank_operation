import pandas as pd
import pytest

from src.services import analyze_cashback_categories


@pytest.fixture
def sample_data_cashback():
    data = {
        "Дата операции": [
            "2023-09-10 12:00:00",
            "2023-09-15 14:30:00",
            "2023-09-20 10:15:00",
            "2023-08-05 09:00:00",  # не сентябрь
        ],
        "Категория": [
            "Food",
            "Food",
            "Transport",
            "Food",
        ],
        "Сумма платежа": [
            200.0,
            300.0,
            100.0,
            150.0,
        ]
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    return df


def test_analyze_cashback_categories_valid_data(sample_data_cashback):
    result = analyze_cashback_categories(sample_data_cashback, 2023, 9)
    expected = {
        "Food": (200 + 300) * 0.05,  # Кэшбэк за Food
        "Transport": (100) * 0.05  # Кэшбэк за Transport
    }

    assert result["Food"] == expected["Food"]
    assert result["Transport"] == expected["Transport"]
    assert len(result) == 2


def test_analyze_cashback_categories_empty_dataframe():
    empty_df = pd.DataFrame(columns=["Дата операции", "Категория", "Сумма платежа"])
    result = analyze_cashback_categories(empty_df, 2023, 9)

    assert result == {}


def test_analyze_cashback_categories_no_transactions_in_month(sample_data_cashback):
    result = analyze_cashback_categories(sample_data_cashback, 2023, 10)  # Нет транзакций в октябре

    assert result == {}


def test_analyze_cashback_categories_invalid_date_type(sample_data_cashback):
    sample_data_invalid_date = sample_data_cashback.copy()
    sample_data_invalid_date['Дата операции'] = sample_data_invalid_date['Дата операции'].astype(
        str)  # Приводим к строкам

    result = analyze_cashback_categories(sample_data_invalid_date, 2023, 9)

    assert result == {}


def test_analyze_cashback_categories_no_date_column(sample_data_cashback):
    sample_data_no_date_column = sample_data_cashback.drop(columns=['Дата операции'])

    result = analyze_cashback_categories(sample_data_no_date_column, 2023, 9)

    assert result == {}


if __name__ == "__main__":
    pytest.main()
