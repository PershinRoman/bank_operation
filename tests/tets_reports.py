import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from src.reports import spending_by_category  # Замените на имя вашего модуля


def test_spending_by_category():
    # Подготовка данных для теста
    data = {
        "Дата операции": [
            "2023-07-31 10:00:00",
            "2023-08-15 12:00:00",
            "2023-09-10 14:00:00",
            "2023-10-05 09:00:00",
            "2023-11-01 18:00:00"
        ],
        "Категория": [
            "Продукты",
            "Продукты",
            "Продукты",
            "Продукты",
            "Продукты"
        ],
        "Сумма платежа": [
            150.0,
            100.0,
            200.0,
            250.0,
            300.0
        ]
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    # Вызов функции с тестовыми данными
    result = spending_by_category(df, "Продукты", "2023-10-31 23:59:59")

    # Ожидаемый результат
    expected_result = {
        "2023-08": 100.0,
        "2023-09": 200.0,
        "2023-10": 250.0
    }

    # Проверка результата
    assert result == expected_result, f"Expected {expected_result}, but got {result}"


@patch("builtins.open", new_callable=MagicMock)
@patch("your_module.logger")  # Замените на путь к вашему логгеру
def test_spending_by_category_with_mocks(mock_logger, mock_open):
    # Подготовка данных для теста
    data = {
        "Дата операции": [
            "2023-07-31 10:00:00",
            "2023-08-15 12:00:00",
            "2023-09-10 14:00:00",
            "2023-10-05 09:00:00",
            "2023-11-01 18:00:00"
        ],
        "Категория": [
            "Продукты",
            "Продукты",
            "Продукты",
            "Продукты",
            "Продукты"
        ],
        "Сумма платежа": [
            150.0,
            100.0,
            200.0,
            250.0,
            300.0
        ]
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    # Вызов функции с тестовыми данными
    result = spending_by_category(df, "Продукты", "2023-10-31 23:59:59")

    # Ожидаемый результат
    expected_result = {
        "2023-08": 100.0,
        "2023-09": 200.0,
        "2023-10": 250.0
    }

    # Проверка результата
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

    # Проверка, что файл был открыт для записи
    mock_open.assert_called_once()

    # Проверка, что логгер был вызван для сохранения отчета
    mock_logger.info.assert_called()


if __name__ == "__main__":
    unittest.main()
