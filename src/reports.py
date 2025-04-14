import json
import logging
import datetime
import pandas as pd
from functools import wraps

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def save_report(filename: str = None):
    """
    Декоратор для записи результатов функции-отчёта в файл.
    Если filename не указан, используется имя по умолчанию: report_<current_date>.txt
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Определяем имя файла
            file_name = filename or f"report_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
            try:
                with open(file_name, "w", encoding="utf-8") as f:
                    # Можно сохранить в виде json, если результат сериализуем
                    f.write(json.dumps(result, indent=2, ensure_ascii=False))
                logger.info(f"Report saved in file: {file_name}")
            except Exception as e:
                logger.error(f"Error saving report: {e}")
            return result

        return wrapper

    return decorator


@save_report()  # Можно указать имя файла: @save_report("название.txt")
def spending_by_category(df: pd.DataFrame, category: str, date_str: str = None) -> dict:
    """
    Возвращает траты по заданной категории за последние три месяца от указанной даты.
    Если date_str не передан, берется текущая дата.

    Формат выходных данных:
    {
      "YYYY-MM": сумма,
      "YYYY-MM": сумма,
      ...
    }
    """
    # Определяем дату анализа
    if date_str:
        try:
            current_date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.error(f"Invalid date format: {date_str}. Expected 'YYYY-MM-DD HH:MM:SS'.")
            current_date = datetime.datetime.now()
    else:
        current_date = datetime.datetime.now()

    # Определяем дату три месяца назад
    # Пример: если текущая дата 2023-10-23, то начало интервала 2023-07-23
    date_3_months_ago = current_date - pd.DateOffset(months=3)

    # Фильтруем DataFrame по дате и категории
    mask = (df["Дата операции"] >= date_3_months_ago) & (df["Дата операции"] <= current_date) & (df["Категория"] == category)
    df_filtered = df[mask].copy()

    if df_filtered.empty:
        logger.info(f"No transactions found for category '{category}' in the last 3 months.")
        return {}

    # Группируем по месяцу и суммируем "Сумма платежа"
    df_filtered["year_month"] = df_filtered["Дата операции"].dt.to_period("M")
    grouped = df_filtered.groupby("year_month")["Сумма платежа"].sum()
    # Приводим индекс к строкам для JSON-совместимого вывода
    result = {str(period): round(amount, 2) for period, amount in grouped.items()}
    return result


if __name__ == '__main__':
    # Пример данных для отчёта
    data = {
        "Дата операции": [
            "2023-07-31 10:00:00",  # входит в интервал
            "2023-08-15 12:00:00",
            "2023-09-10 14:00:00",
            "2023-10-05 09:00:00",
            "2023-11-01 18:00:00"  # вне интервала
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

    report = spending_by_category(df, "Продукты", "2023-10-31 23:59:59")
    print(json.dumps(report, indent=2, ensure_ascii=False))
