import pytest
import pandas as pd
import datetime
from unittest.mock import patch, mock_open
from src.main import load_user_settings, main, get_greeting, get_card_stats, get_top_transactions, \
    get_currency_rates, get_stock_prices


# Тест для функции load_user_settings
def test_load_user_settings_valid():
    mock_data = '{"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "GOOGL"]}'
    with patch("builtins.open", mock_open(read_data=mock_data)):
        settings = load_user_settings('dummy_path.json')
        assert settings == {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "GOOGL"]
        }


def test_load_user_settings_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        settings = load_user_settings('dummy_path.json')
        assert settings == {}


def test_load_user_settings_json_decode_error():
    with patch("builtins.open", mock_open(read_data='invalid json')):
        settings = load_user_settings('dummy_path.json')
        assert settings == {}


# Тест для функции get_greeting
def test_get_greeting():
    assert get_greeting(datetime.time(6, 0)) == 'Доброе утро'
    assert get_greeting(datetime.time(13, 0)) == 'Добрый день'
    assert get_greeting(datetime.time(18, 0)) == 'Добрый вечер'
    assert get_greeting(datetime.time(23, 0)) == 'Доброй ночи'


# Тест для функции get_card_stats
def test_get_card_stats():
    data = {
        'Номер карты': [1234567890123456, 1234567890123456, 9876543210123456],
        'Сумма платежа': [100.0, 200.0, 150.0]
    }
    df = pd.DataFrame(data)
    result = get_card_stats(df)

    expected = {
        '3456': {'total_spent': 300.0, 'cashback': 3},
        '3456': {'total_spent': 150.0, 'cashback': 1}
    }

    assert result['3456']['total_spent'] == expected['3456']['total_spent']
    assert result['3456']['cashback'] == expected['3456']['cashback']


# Тест для функции get_top_transactions
def test_get_top_transactions():
    data = {
        'Дата операции': ['2023-10-01', '2023-10-02', '2023-10-03', '2023-10-04', '2023-10-05'],
        'Описание': ['Transaction1', 'Transaction2', 'Transaction3', 'Transaction4', 'Transaction5'],
        'Сумма платежа': [100.0, 200.0, 300.0, 400.0, 500.0]
    }
    df = pd.DataFrame(data)

    result = get_top_transactions(df)

    assert len(result) == 5
    assert result[0]['Сумма платежа'] == 500.0


def test_get_currency_rates_no_currencies():
    rates = get_currency_rates([])

    assert rates == {}


def test_get_stock_prices_no_stocks():
    prices = get_stock_prices([])

    assert prices == {}


# Тест для основной функции main (с использованием mock'ов)
@patch('pandas.read_excel')
@patch('src.main.load_user_settings')
@patch('src.main.get_card_stats')
@patch('src.main.get_top_transactions')
@patch('src.main.get_currency_rates')
@patch('src.main.get_stock_prices')
def test_main(mock_stock_prices, mock_currency_rates, mock_top_transactions,
              mock_card_stats, mock_load_user_settings,
              mock_read_excel):
    # Настройка моков
    mock_read_excel.return_value = pd.DataFrame({
        'Дата операции': ['2023-10-01', '2023-10-02'],
        'Номер карты': [1234567890123456] * 2,
        'Сумма платежа': [100.0] * 2,
        'Описание': ['Test1', 'Test2']
    })

    mock_load_user_settings.return_value = {}
    mock_card_stats.return_value = {}
    mock_top_transactions.return_value = []
    mock_currency_rates.return_value = {}
    mock_stock_prices.return_value = {}

    result = main('2023-10-02 12:00:00')

    assert isinstance(result, dict)


if __name__ == '__main__':
    pytest.main()
