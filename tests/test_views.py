import unittest
from unittest.mock import patch, mock_open
import pandas as pd
import datetime
import json

from src.views import (
    start_of_month,
    load_user_settings,
    read_excel_data,
    get_greeting,
    get_card_info,
    get_top_transactions,
    get_currency_rates,
    get_stock_prices,
)


def test_start_of_month():
    dt = datetime.datetime(2023, 10, 15)
    result = start_of_month(dt)
    expected = datetime.datetime(2023, 10, 1, 0, 0, 0)
    assert result == expected


@patch("builtins.open", new_callable=mock_open,
       read_data='{"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "GOOGL"]}')
def test_load_user_settings(mock_file):
    result = load_user_settings("dummy_path")
    expected = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "GOOGL"]
    }
    assert result == expected


@patch("pandas.read_excel")
def test_read_excel_data(mock_read_excel):
    mock_read_excel.return_value = pd.DataFrame({
        'Дата операции': ['2023-10-01', '2023-10-02'],
        'Номер карты': ['1234 5678 9012 3456', '1234 5678 9012 3457'],
        'Сумма платежа': [100.0, 200.0],
        'Описание': ['Тестовая транзакция', 'Еще одна транзакция'],
        'Категория': ['Еда', 'Транспорт']
    })

    result = read_excel_data("dummy_path.xlsx")
    assert len(result) == 2
    assert result['Номер карты'][0] == '1234 5678 9012 3456'


def test_get_greeting():
    morning_time = datetime.time(6, 0)
    afternoon_time = datetime.time(13, 0)
    evening_time = datetime.time(18, 0)
    night_time = datetime.time(23, 0)

    assert get_greeting(morning_time) == "Доброе утро"
    assert get_greeting(afternoon_time) == "Добрый день"
    assert get_greeting(evening_time) == "Добрый вечер"
    assert get_greeting(night_time) == "Доброй ночи"


def test_get_card_info():
    df = pd.DataFrame({
        'Номер карты': ['1234 5678 9012 3456', '1234 5678 9012 3457'],
        'Сумма платежа': [100.0, 200.0]
    })

    result = get_card_info(df)

    expected = [
        {'last_digits': '3456', 'total_spent': 100.0, 'cashback': 1.0},
        {'last_digits': '3457', 'total_spent': 200.0, 'cashback': 2.0}
    ]

    assert result == expected


def test_get_top_transactions():
    df = pd.DataFrame({
        'Дата операции': [datetime.datetime(2023, 10, 1), datetime.datetime(2023, 10, 2)],
        'Сумма платежа': [100.0, 200.0],
        'Категория': ['Еда', 'Транспорт'],
        'Описание': ['Тестовая транзакция', 'Еще одна транзакция']
    })

    result = get_top_transactions(df)

    expected = [
        {'date': '02.10.2023', 'amount': 200.0, 'category': 'Транспорт', 'description': 'Еще одна транзакция'},
        {'date': '01.10.2023', 'amount': 100.0, 'category': 'Еда', 'description': 'Тестовая транзакция'}
    ]

    assert result[0]['amount'] == expected[0]['amount']


@patch('requests.get')
def test_get_currency_rates(mock_get):
    # Мокируем ответ API
    mock_get.return_value.json.return_value = {
        "rates": {
            "USD": 75.5,
            "EUR": 0.883,
            # Допустим, GBP отсутствует
        }
    }

    result = get_currency_rates(['USD', 'EUR', 'GBP'])

    expected = [
        {"currency": "USD", "rate": 75.5},
        {"currency": "EUR", "rate": 0.883},
        {"currency": "GBP", "rate": "Not available"}  # Ожидаем строку "Not available" для GBP
    ]

    assert result == expected


@patch('requests.Session.get')
def test_get_stock_prices(mock_get):
    mock_get.return_value.json.return_value = {
        "Global Quote": {
            "05. price": "150.00"
        }
    }

    result = get_stock_prices(['AAPL'])

    expected = [{"stock": "AAPL", "price": 150.00}]

    assert result[0]['price'] == expected[0]['price']


if __name__ == "__main__":
    # Запуск всех тестов
    test_start_of_month()
    test_load_user_settings()
    test_read_excel_data()
    test_get_greeting()
    test_get_card_info()
    test_get_top_transactions()
    test_get_currency_rates()
    test_get_stock_prices()

    print("Все тесты пройдены успешно!")
