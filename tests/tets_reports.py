import os
import datetime
import pandas as pd
import pytest

from  src.reports import spending_by_category, save_report


@pytest.fixture
def sample_transactions():
    """
    Формирует тестовый DataFrame с данными по транзакциям.
    """
    data = {
        # Даты расположены так, чтобы проверить попадание в интервал [date - 3 месяца, date]
        "Дата операции": [
            "2023-07-31 10:00:00",  # ровно 3 месяца назад (включительно)
            "2023-08-15 12:00:00",
            "2023-09-10 14:00:00",
            "2023-10-05 09:00:00",
            "2023-11-01 18:00:00"  # вне интервала – позже указанной даты
        ],
        "Категория": [
            "Продукты",  # попадает
            "Продукты",  # попадает
            "Продукты",  # попадает
            "Продукты",  # попадает, если тестовая дата '2023-10-31'
            "Продукты"  # не должен попасть – дата позже тестовой даты
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
    # Приводим столбец с датами к типу datetime
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    return df


def test_spending_by_category_with_explicit_date(sample_transactions):
    """
    Проверяем, что функция корректно фильтрует транзакции за последние 3 месяца от заданной даты.
    """
    # Установим тестовую дату: 2023-10-31
    test_date = "2023-10-31 23:59:59"
    result = spending_by_category(sample_transactions, "Продукты", test_date)

    # Ожидаемые транзакции: строки с датами 2023-07-31, 2023-08-15, 2023-09-10 и 2023-10-05.
    # Группировка по месяцу даст следующие суммы:
    # 2023-07: 150.0
    # 2023-08: 100.0
    # 2023-09: 200.0
    # 2023-10: 250.0
    expected_index = pd.period_range(start="2023-07", end="2023-10", freq='M')
    expected_values = [150.0, 100.0, 200.0, 250.0]
    expected_series = pd.Series(data=expected_values, index=expected_index).round(2)

    # Приводим индексы в результате к строковому представлению для удобства сравнения
    pd.testing.assert_series_equal(result, expected_series)


def test_spending_by_category_with_default_date(sample_transactions):
    """
    Проверяем работу функции, если аргумент date не передан.
    Здесь мы не можем точно задать ожидаемое значение, но можем проверить,
    что возвращаемая Series имеет тип PeriodIndex и не содержит транзакций за будущее.
    """
    result = spending_by_category(sample_transactions, "Продукты")
    # Получаем текущую дату и вычисляем дату 3 месяца назад
    current_date = pd.to_datetime('today')
    date_3_months_ago = current_date - pd.DateOffset(months=3)

    # Проверяем, что в результате не попали транзакции, позже текущей даты
    assert result.index.max() <= current_date.to_period('M')


# --- Тест для декоратора save_report ---

def test_save_report(tmp_path):
    """
    Проверяем работу декоратора save_report: функция должна вернуть результат
    и создать файл отчёта с корректным содержимым.
    """

    # Определяем временную функцию, декорированную save_report
    @save_report
    def dummy_report(a, b):
        return {"result": a + b}

    # Задаём параметры
    a, b = 5, 7
    result = dummy_report(a, b)

    # Проверяем, что результат корректный
    assert result == {"result": 12}

    # Формируем ожидаемое имя файла
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f"dummy_report_report_{today_str}.txt"
    file_path = tmp_path / filename

    # Поскольку декоратор создаёт файл в рабочей директории,
    # переименовываем его в tmp_path для тестирования:
    # 1. Проверим, что файл существует в текущей директории.
    assert os.path.exists(filename), f"Файл {filename} не найден в рабочей директории."

    # 2. Открываем и проверяем содержимое файла
    with open(filename, 'r', encoding='utf-8') as f:
        file_content = f.read()
    assert file_content == str(result)

    # Очистка: удаляем созданный файл
    os.remove(filename)
