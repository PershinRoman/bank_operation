import os
import tempfile
import pandas as pd
import pytest
import requests

from src.utils import read_excel_data, fetch_data_from_api


def test_read_excel_data_valid():
    """
    Проверяем, что функция read_excel_data корректно считывает Excel-файл
    и приводит столбец 'Дата операции' к формату datetime.
    """
    # Создаем тестовый DataFrame
    df_expected = pd.DataFrame({
        "Дата операции": ["2023-10-01 10:00:00", "2023-10-02 12:30:00"],
        "Сумма платежа": [100.0, 200.0]
    })
    df_expected["Дата операции"] = pd.to_datetime(df_expected["Дата операции"])

    # Сохраняем DataFrame во временный Excel-файл
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        test_filepath = tmp.name
    try:
        df_expected.to_excel(test_filepath, index=False)
        # Вызываем функцию чтения
        df_result = read_excel_data(test_filepath)
        # Проверяем, что столбец 'Дата операции' имеет тип datetime
        assert pd.api.types.is_datetime64_any_dtype(df_result["Дата операции"]), \
            "Столбец 'Дата операции' должен иметь тип datetime"

        # Сравниваем DataFrame, игнорируя различия в типах данных столбцов
        pd.testing.assert_frame_equal(
            df_result.reset_index(drop=True),
            df_expected.reset_index(drop=True),
            check_dtype=False
        )
    finally:
        os.remove(test_filepath)


def test_read_excel_data_file_not_found():
    """
    Проверяем, что функция read_excel_data генерирует FileNotFoundError при отсутствии файла.
    """
    invalid_filepath = "non_existent_file.xlsx"
    with pytest.raises(FileNotFoundError):
        read_excel_data(invalid_filepath)


class DummyResponse:
    """
    Класс-имитация ответа requests.
    """
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code} Error")


def test_fetch_data_from_api_success(monkeypatch):
    """
    Проверяем, что fetch_data_from_api возвращает корректный словарь при успешном запросе.
    """
    # Подготовим тестовые данные
    dummy_json = {"key": "value"}

    def fake_get(url, params=None, timeout=10):
        return DummyResponse(dummy_json, status_code=200)

    # Заменяем requests.get на нашу фабрику
    monkeypatch.setattr(requests, "get", fake_get)

    url = "http://example.com/api"
    result = fetch_data_from_api(url)
    assert result == dummy_json, "При успешном запросе функция должна вернуть корректный JSON"


def test_fetch_data_from_api_failure(monkeypatch):
    """
    Проверяем, что в случае ошибки запроса fetch_data_from_api возвращает пустой словарь.
    """
    def fake_get(url, params=None, timeout=10):
        raise requests.exceptions.RequestException("Network error")

    monkeypatch.setattr(requests, "get", fake_get)

    url = "http://example.com/api"
    result = fetch_data_from_api(url)
    assert result == {}, "При ошибке запроса функция должна возвращать пустой словарь"
