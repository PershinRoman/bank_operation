import json
import logging
import datetime
import pandas as pd
import requests

# Настройка логгера
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def load_user_settings(filepath: str) -> dict:
    """
    Загружает пользовательские настройки (валюты, акции и т.д.) из JSON-файла.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            logger.info(f"User settings loaded from {filepath}")
            return settings
    except FileNotFoundError:
        logger.error(f"Settings file {filepath} not found.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding user settings JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error reading {filepath}: {e}")
        return {}


def get_greeting(time: datetime.time) -> str:
    """
    Возвращает приветствие в зависимости от времени суток.
    """
    if datetime.time(5, 0) <= time < datetime.time(12, 0):
        return 'Доброе утро'
    elif datetime.time(12, 0) <= time < datetime.time(17, 0):
        return 'Добрый день'
    elif datetime.time(17, 0) <= time < datetime.time(23, 0):
        return 'Добрый вечер'
    return 'Доброй ночи'


def get_card_info(df: pd.DataFrame) -> list:
    """
    Группирует транзакции по карте и рассчитывает сумму расходов и кэшбэк.
    Кэшбэк – 1 рубль на каждые 100 рублей (вычисляется как сумма/100 с точностью до двух знаков).
    Возвращает список словарей.
    """
    result = []
    if df.empty:
        return result
    grouped = df.groupby('Номер карты')['Сумма платежа'].sum()
    for card_number, total_spent in grouped.items():
        last_digits = str(card_number)[-4:]
        cashback = round(total_spent / 100, 2)
        result.append({
            "last_digits": last_digits,
            "total_spent": round(total_spent, 2),
            "cashback": cashback
        })
    return result


def get_top_transactions(df: pd.DataFrame) -> list:
    """
    Выбирает до 5 транзакций с наибольшей суммой платежа.
    В результирующий словарь включаются: дата (в формате DD.MM.YYYY), сумма, категория и описание.
    """
    if df.empty:
        return []
    top_df = df.nlargest(5, 'Сумма платежа')
    result = []
    for _, row in top_df.iterrows():
        result.append({
            "date": pd.to_datetime(row["Дата операции"]).strftime("%d.%m.%Y"),
            "amount": round(row["Сумма платежа"], 2),
            "category": row.get("Категория", ""),
            "description": row.get("Описание", "")
        })
    return result


def get_currency_rates(currencies: list) -> list:
    """
    Получает курсы указанных валют по отношению к рублю.
    Использует бесплатное API: https://api.exchangerate-api.com/v4/latest/RUB
    Возвращает список словарей с полями "currency" и "rate".
    """
    if not currencies:
        return []
    url = "https://api.exchangerate-api.com/v4/latest/RUB"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Error fetching currency rates: {e}")
        return []
    all_rates = data.get("rates", {})
    result = []
    for curr in currencies:
        rate = all_rates.get(curr, "Not available")
        result.append({
            "currency": curr,
            "rate": rate
        })
    return result


def get_stock_prices(stocks: list) -> list:
    """
    Получает текущие цены акций.
    Для демонстрации используется API Alpha Vantage.
    Не забудьте заменить YOUR_API_KEY на действительный API-ключ.
    Возвращает список словарей с полями "stock" и "price".
    """
    if not stocks:
        return []
    api_key = "YOUR_API_KEY"
    base_url = "https://www.alphavantage.co/query"
    result = []
    for symbol in stocks:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": api_key
        }
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            price = data.get("Global Quote", {}).get("05. price", "Not available")
        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {e}")
            price = "Not available"
        result.append({
            "stock": symbol,
            "price": float(price) if isinstance(price, str) and price.replace('.', '', 1).isdigit() else price
        })
    return result


def read_excel_data(filepath: str) -> pd.DataFrame:
    """
    Считывает данные из Excel по указанному пути.
    Ожидается, что файл содержит столбцы: 'Дата операции', 'Номер карты', 'Сумма платежа', 'Описание', 'Категория'.
    """
    try:
        df = pd.read_excel(filepath)
        # Приведение столбца дат к datetime
        df["Дата операции"] = pd.to_datetime(df["Дата операции"])
        return df
    except Exception as e:
        logger.error(f"Error reading Excel file {filepath}: {e}")
        return pd.DataFrame()


def main(date_str: str) -> dict:
    """
    Главная функция для формирования JSON-ответа веб-страницы «Главная».
    Принимает строку с датой и временем в формате 'YYYY-MM-DD HH:MM:SS'.
    Данные для анализа – транзакции с начала месяца до заданной даты.
    """
    try:
        input_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        logger.error(f"Invalid date format: {date_str}. Expected 'YYYY-MM-DD HH:MM:SS'.")
        return {}

    # Приветствие
    greeting = get_greeting(input_dt.time())

    # Считываем данные из Excel (например, data/operations.xls)
    df = read_excel_data("data/operations.xls")
    if df.empty:
        logger.warning("No transaction data available.")

    # Фильтруем данные: с начала месяца до указанной даты
    start_of_month = input_dt.replace(day=1, hour=0, minute=0, second=0)
    df_filtered = df[(df["Дата операции"] >= start_of_month) & (df["Дата операции"] <= input_dt)]

    # Формируем информацию по картам
    cards = get_card_info(df_filtered)

    # Топ-5 транзакций
    top_transactions = get_top_transactions(df_filtered)

    # Загружаем настройки из файла
    user_settings = load_user_settings("user_settings.json")
    currencies = user_settings.get("user_currencies", [])
    stocks = user_settings.get("user_stocks", [])

    currency_rates = get_currency_rates(currencies)
    stock_prices = get_stock_prices(stocks)

    result = {
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices
    }

    # Возвращаем JSON-совместимый словарь
    return result


if __name__ == '__main__':
    # Пример вызова
    input_date_str = "2023-10-23 14:30:00"
    response = main(input_date_str)
    print(json.dumps(response, indent=2, ensure_ascii=False))
