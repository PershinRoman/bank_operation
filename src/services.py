import json
import logging
import pandas as pd
import pytest

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def analyze_cashback_categories(data: pd.DataFrame, year: int, month: int) -> dict:
    """
    Анализирует, сколько кешбэка можно заработать по каждой категории в указанном месяце.
    На вход подаётся DataFrame с транзакциями (ожидаются столбцы 'Дата операции', 'Категория', 'Сумма платежа'),
    год и месяц для анализа.

    Кэшбэк считается как сумма/100 для каждой транзакции.

    Выходной формат:
    {
        "Категория 1": cashback1,
        "Категория 2": cashback2,
         ...
    }
    """
    if data.empty or 'Дата операции' not in data.columns:
        return {}

        # Убедимся, что столбец 'Дата операции' имеет тип datetime
    if not pd.api.types.is_datetime64_any_dtype(data['Дата операции']):
        return {}

    filtered_df = data[(data['Дата операции'].dt.year == year) & (data['Дата операции'].dt.month == month)]

    # Группируем по категории и суммируем
    cashback = filtered_df.groupby('Категория')['Сумма платежа'].sum() * 0.05

    return cashback.to_dict()


@pytest.fixture
def sample_data_cashback():
    """
    Фикстура, возвращающая тестовый DataFrame для функции analyze_cashback_categories.

    Структура:
    - 'Дата операции': даты транзакций.
    - 'Категория': название категории.
    - 'Сумма платежа': сумма платежа.

    Для сентября 2023 года используем следующие данные:
      - Две транзакции в категории "Food": 200 и 300 → сумма = 500
      - Одна транзакция в категории "Transport": 100
      - Одна транзакция в другой категории и/или другого месяца – не попадёт в анализ.
    """
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
    # Приведем столбец дат к типу datetime
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    return df


# Пример вызова анализа — можно добавить дополнительные функции для других сервисов.
if __name__ == '__main__':
    # Для демонстрации создаём тестовый DataFrame
    data = {
        "Дата операции": ["2023-10-05 10:00:00", "2023-10-15 12:00:00", "2023-10-20 14:00:00", "2023-09-30 18:00:00"],
        "Категория": ["Продукты", "Развлечения", "Продукты", "Топливо"],
        "Сумма платежа": [1500, 500, 800, 1000]
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    analysis = analyze_cashback_categories(df, 2023, 10)
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
