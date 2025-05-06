import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.utils import read_excel_data, fetch_data_from_api


def test_read_excel_data_success():
    # Создаем тестовый DataFrame
    test_data = {
        "Column1": [1, 2, 3],
        "Column2": ["A", "B", "C"]
    }
    test_df = pd.DataFrame(test_data)

    # Мокаем pd.read_excel
    with patch('pandas.read_excel', return_value=test_df) as mock_read_excel:
        result = read_excel_data("test.xlsx")
        mock_read_excel.assert_called_once_with("test.xlsx")
        pd.testing.assert_frame_equal(result, test_df)


def test_read_excel_data_failure():
    # Мокаем pd.read_excel для генерации исключения
    with patch('pandas.read_excel', side_effect=Exception("File not found")):
        result = read_excel_data("non_existent_file.xlsx")
        assert result.empty  # Ожидаем пустой DataFrame


def test_fetch_data_from_api_success():
    # Создаем мок ответа API
    mock_response = MagicMock()
    mock_response.json.return_value = {"key": "value"}

    with patch('requests.get', return_value=mock_response) as mock_get:
        result = fetch_data_from_api("http://example.com/api", params={"param1": "value1"})
        mock_get.assert_called_once_with("http://example.com/api", params={"param1": "value1"}, timeout=10)
        assert result == {"key": "value"}


def test_fetch_data_from_api_failure():
    # Мокаем requests.get для генерации исключения
    with patch('requests.get', side_effect=Exception("Network error")):
        result = fetch_data_from_api("http://example.com/api")
        assert result == {}  # Ожидаем пустой словарь


if __name__ == "__main__":
    pytest.main()
