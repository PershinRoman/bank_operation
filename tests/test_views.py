import json
import pandas as pd
import requests


from src.views import (
    get_greeting,
    get_card_info,
    get_top_transactions,
    get_currency_rates,
    get_stock_prices,
    main
)


def test_get_greeting_morning():
    assert get_greeting("2023-10-20 06:00:00") == "Доброе утро"


def test_get_greeting_afternoon():
    assert get_greeting("2023-10-20 13:00:00") == "Добрый день"


def test_get_greeting_evening():
    assert get_greeting("2023-10-20 19:00:00") == "Добрый вечер"


def test_get_greeting_night():
    assert get_greeting("2023-10-20 03:00:00") == "Доброй ночи"


def test_get_card_info():
    # Создаем тестовый DataFrame с транзакциями по картам
    data = {
        "Номер карты": [1234567890123456, 1234567890123456, 9876543210987654],
        "Сумма платежа": [150.0, 250.0, 300.0]
    }
    df = pd.DataFrame(data)
    # Ожидаем: для карты, последние 4 цифры "3456": сумма 400, cashback = 400 // 100 = 4;
    # для "7654": сумма 300, cashback = 300 // 100 = 3.
    expected = {
        "3456": {"total_spent": 400.0, "cashback": 4},
        "7654": {"total_spent": 300.0, "cashback": 3}
    }
    result = get_card_info(df)
    assert result == expected


def test_get_top_transactions():
    data = {
        "Дата операции": ["2023-10-20", "2023-10-21", "2023-10-22", "2023-10-23", "2023-10-24", "2023-10-25"],
        "Описание": ["A", "B", "C", "D", "E", "F"],
        "Сумма платежа": [100, 300, 200, 400, 50, 350]
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    # Ожидаем, что топ-5 транзакций (по убыванию суммы) будут:
    expected = [
        {"Дата операции": pd.Timestamp("2023-10-23"), "Описание": "D", "Сумма платежа": 400},
        {"Дата операции": pd.Timestamp("2023-10-25"), "Описание": "F", "Сумма платежа": 350},
        {"Дата операции": pd.Timestamp("2023-10-21"), "Описание": "B", "Сумма платежа": 300},
        {"Дата операции": pd.Timestamp("2023-10-22"), "Описание": "C", "Сумма платежа": 200},
        {"Дата операции": pd.Timestamp("2023-10-20"), "Описание": "A", "Сумма платежа": 100},
    ]
    result = get_top_transactions(df)
    assert result == expected


class DummyExchangeResponse:
    """Класс-имитатор объекта ответа от API курсов валют."""
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.HTTPError("HTTP Error")


def dummy_get_currency(url, params=None, timeout=10):
    dummy_data = {
        "rates": {
            "USD": 0.013,
            "EUR": 0.011
        }
    }
    return DummyExchangeResponse(dummy_data, status_code=200)


def test_get_currency_rates(monkeypatch):
    monkeypatch.setattr(requests, "get", dummy_get_currency)
    currencies = ["USD", "EUR", "GBP"]
    result = get_currency_rates(currencies)
    expected = {"USD": 0.013, "EUR": 0.011, "GBP": "Not available"}
    assert result == expected


class DummyStockResponse:
    """Класс-имитатор ответа API для акций."""
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data


def dummy_get_stock(url, params=None, timeout=10):
    # Для упрощения, возвращаем цену как строку "150.0" для любого тикера.
    dummy_data = {
        "Global Quote": {
            "05. price": "150.0"
        }
    }
    return DummyStockResponse(dummy_data, status_code=200)


def test_get_stock_prices(monkeypatch):
    monkeypatch.setattr(requests, "get", dummy_get_stock)
    stocks = ["AAPL", "GOOGL"]
    result = get_stock_prices(stocks)
    expected = {"AAPL": "150.0", "GOOGL": "150.0"}
    assert result == expected


def test_main(monkeypatch, tmp_path):
    """
    Для функции main создаём временный Excel-файл и файл с настройками.
    Подменяем внешние вызовы API и чтение файлов.
    """
    # Создаем временный Excel-файл, имитирующий operations.xls
    df = pd.DataFrame({
        "Дата операции": ["2023-10-01 10:00:00", "2023-10-15 12:00:00", "2023-10-20 14:00:00"],
        "Номер карты": [1111222233334444, 1111222233334444, 5555666677778888],
        "Сумма платежа": [150, 200, 300],
        "Описание": ["Test1", "Test2", "Test3"]
    })
    excel_file = tmp_path / "operations.xls"
    df.to_excel(excel_file, index=False)

    # Создаем временный файл user_settings.json
    user_settings = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "GOOGL"]
    }
    settings_file = tmp_path / "user_settings.json"
    settings_file.write_text(json.dumps(user_settings), encoding="utf-8")

    # Подменяем pd.read_excel: всегда читаем наш временный Excel вне зависимости от переданного пути
    def fake_read_excel(filepath, *args, **kwargs):
        return pd.read_excel(excel_file)
    monkeypatch.setattr(pd, "read_excel", fake_read_excel)

    # Подменяем open для user_settings.json: если запрашиваем именно файл настроек, открываем наш временный файл.
    def fake_open(filepath, *args, **kwargs):
        if filepath == "user_settings.json":
            return open(settings_file, *args, **kwargs)
        else:
            return open(filepath, *args, **kwargs)
    monkeypatch.setattr("builtins.open", fake_open)

    # Подменяем requests.get для обоих вызовов API
    def fake_requests_get(url, params=None, timeout=10):
        if "exchangerate-api" in url:
            # Возвращаем данные для курсов валют
            return DummyExchangeResponse({
                "rates": {
                    "USD": 0.013,
                    "EUR": 0.011
                }
            }, status_code=200)
        else:
            # Для акций
            return DummyStockResponse({
                "Global Quote": {
                    "05. price": "150.0"
                }
            }, status_code=200)
    monkeypatch.setattr(requests, "get", fake_requests_get)

    # Передаём дату, которая лежит в октябре, чтобы данные корректно отфильтровались (с начала месяца до указанной даты)
    result_json = main("2023-10-20 14:30:00")
    result = json.loads(result_json)

    # Проверяем приветствие.
    # 14:30 относится к дню, поэтому ожидаем "Добрый день"
    assert result["greeting"] == "Добрый день"

    # Проверяем информацию по картам.
    # В исходном файле две карты:
    # - Карта 1111222233334444 (оканчивается на "4444"): транзакции 150 и 200 → сумма 350, cashback = 350 // 100 = 3
    # - Карта 5555666677778888 (оканчивается на "8888"): транзакция 300 → cashback = 3
    expected_cards = {
        "4444": {"total_spent": 350.0, "cashback": 3},
        "8888": {"total_spent": 300.0, "cashback": 3}
    }
    assert result["cards"] == expected_cards

    # Проверяем топ-транзакции. Они должны быть отсортированы по 'Сумма платежа' в порядке убывания.
    expected_top = [
        {
            "Дата операции": pd.Timestamp("2023-10-20 14:00:00").isoformat(),
            "Описание": "Test3",
            "Сумма платежа": 300
        },
        {
            "Дата операции": pd.Timestamp("2023-10-15 12:00:00").isoformat(),
            "Описание": "Test2",
            "Сумма платежа": 200
        },
        {
            "Дата операции": pd.Timestamp("2023-10-01 10:00:00").isoformat(),
            "Описание": "Test1",
            "Сумма платежа": 150
        }
    ]
    # Преобразуем дату в ISO-формат, так как JSON при сериализации Timestamps выдаёт строки.
    top_from_main = result["top_transactions"]
    # Приводим дату из результата к isoформату для сравнения
    for tr in top_from_main:
        tr["Дата операции"] = pd.Timestamp(tr["Дата операции"]).isoformat()
    assert top_from_main == expected_top

    # Проверяем курсы валют и цены акций
    expected_currency = {"USD": 0.013, "EUR": 0.011}
    expected_stock = {"AAPL": "150.0", "GOOGL": "150.0"}
    assert result["currency_rates"] == expected_currency
    assert result["stock_prices"] == expected_stock
