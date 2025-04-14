import json
import logging
import pandas as pd

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
    # Фильтруем транзакции по году и месяцу
    df_filtered = data[(data["Дата операции"].dt.year == year) & (data["Дата операции"].dt.month == month)]
    if df_filtered.empty:
        logger.info(f"Нет данных за {year}-{month:02d}")
        return {}

    # Функциональный стиль: сгруппировать по категории и посчитать сумму кешбэка (каждые 100 = 1 рубль)
    grouped = df_filtered.groupby("Категория")["Сумма платежа"].sum()
    result = grouped.apply(lambda x: round(x / 100, 2)).to_dict()

    return result


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
