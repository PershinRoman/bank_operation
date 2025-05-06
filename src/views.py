import os
import json
import logging
import datetime
from typing import List, Dict, Any, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Конфигурация через ENV ---
OPERATIONS_FILE = os.getenv("OPERATIONS_FILE", "data/operations.xlsx")
USER_SETTINGS_FILE = os.getenv("USER_SETTINGS_FILE", "user_settings.json")
CURRENCY_API_URL = os.getenv("CURRENCY_API_URL", "https://api.exchangerate-api.com/v4/latest/RUB")
STOCK_API_URL = os.getenv("STOCK_API_URL", "https://www.alphavantage.co/query")
STOCK_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "YOUR_API_KEY")

# --- Логгирование ---
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# --- HTTP сессия с ретраями ---
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)


def start_of_month(dt: datetime.datetime) -> datetime.datetime:
    """
    Возвращает начало месяца для заданной даты.

    Args:
        dt (datetime.datetime): исходная дата.

    Returns:
        datetime.datetime: дата и время первого дня месяца, 00:00:00.
    """
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def load_user_settings(filepath: str) -> Dict[str, List[str]]:
    """
    Загружает настройки пользователя из JSON-файла.

    Args:
        filepath (str): путь к файлу настроек.

    Returns:
        dict: словарь с ключами 'user_currencies' и 'user_stocks'.
    """
    defaults = {"user_currencies": [], "user_stocks": []}
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        curr = data.get("user_currencies")
        stocks = data.get("user_stocks")
        if not isinstance(curr, list) or not isinstance(stocks, list):
            raise ValueError("Invalid format in user settings")
        return {"user_currencies": curr, "user_stocks": stocks}
    except FileNotFoundError:
        logger.warning(f"User settings file not found: {filepath}")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing user settings: {e}")
    except Exception as e:
        logger.error(f"Unexpected error reading {filepath}: {e}")
    return defaults


def read_excel_data(filepath: str) -> pd.DataFrame:
    """
    Считывает операции из Excel-файла.

    Args:
        filepath (str): путь к Excel файлу.

    Returns:
        pd.DataFrame: датафрейм с колонками 'Дата операции', 'Номер карты', 'Сумма платежа', 'Описание', 'Категория'.
    """
    try:
        df = pd.read_excel(
            filepath,
            usecols=['Дата операции', 'Номер карты', 'Сумма платежа', 'Описание', 'Категория']
        )
        df['Дата операции'] = pd.to_datetime(df['Дата операции'], errors='coerce')
        return df.dropna(subset=['Дата операции'])
    except Exception as e:
        logger.error(f"Error reading Excel '{filepath}': {e}")
        return pd.DataFrame(columns=['Дата операции', 'Номер карты', 'Сумма платежа', 'Описание', 'Категория'])


def get_greeting(time: datetime.time) -> str:
    """
    Возвращает приветствие в зависимости от времени суток.

    Args:
        time (datetime.time): текущее время.

    Returns:
        str: приветствие.
    """
    if datetime.time(5, 0) <= time < datetime.time(12, 0):
        return "Доброе утро"
    if datetime.time(12, 0) <= time < datetime.time(17, 0):
        return "Добрый день"
    if datetime.time(17, 0) <= time < datetime.time(23, 0):
        return "Добрый вечер"
    return "Доброй ночи"


def get_card_info(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Группирует транзакции по картам и считает сумму расходов и кэшбэк.

    Args:
        df (pd.DataFrame): датафрейм с транзакциями.

    Returns:
        list: список словарей с ключами 'last_digits', 'total_spent', 'cashback'.
    """
    if df.empty:
        return []
    summary = (
        df.groupby("Номер карты", as_index=False)["Сумма платежа"]
        .sum()
        .rename(columns={"Сумма платежа": "total_spent"})
    )
    summary["cashback"] = (summary["total_spent"] / 100).round(2)
    out = []
    for _, row in summary.iterrows():
        card_str = str(row["Номер карты"])
        out.append({
            "last_digits": card_str[-4:],
            "total_spent": round(float(row["total_spent"]), 2),
            "cashback": float(row["cashback"])
        })
    return out


def get_top_transactions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Выбирает до 5 крупнейших транзакций.

    Args:
        df (pd.DataFrame): датафрейм с транзакциями.

    Returns:
        list: список словарей с датой, суммой, категорией и описанием.
    """
    if df.empty:
        return []
    top5 = df.nlargest(5, "Сумма платежа")
    res = []
    for _, r in top5.iterrows():
        res.append({
            "date": r["Дата операции"].strftime("%d.%m.%Y"),
            "amount": round(float(r["Сумма платежа"]), 2),
            "category": r.get("Категория", "") or "",
            "description": r.get("Описание", "") or ""
        })
    return res


def get_currency_rates(currencies):
    rates = []
    response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")  # Замените на реальный URL
    data = response.json()

    for currency in currencies:
        rate = data.get("rates", {}).get(currency)
        if rate is None:
            rate = "Not available"
        rates.append({"currency": currency, "rate": rate})

    return rates


def get_stock_prices(stocks: List[str],
                     api_key: str = STOCK_API_KEY,
                     base_url: str = STOCK_API_URL) -> List[Dict[str, Any]]:
    """
    Запрашивает текущие цены акций через API Alpha Vantage.

    Args:
        stocks (list): список тикеров.
        api_key (str): API ключ.
        base_url (str): URL API.

    Returns:
        list: список словарей с 'stock' и 'price'.
    """
    if not stocks:
        return []
    out = []
    for sym in stocks:
        params = {"function": "GLOBAL_QUOTE", "symbol": sym, "apikey": api_key}
        price: Optional[float] = None
        try:
            resp = session.get(base_url, params=params, timeout=10)
            resp.raise_for_status()
            quote = resp.json().get("Global Quote", {})
            p = quote.get("05. price")
            price = float(p) if p is not None else None
        except (requests.RequestException, ValueError) as e:
            logger.error(f"Error fetching price for {sym}: {e}")
        out.append({"stock": sym, "price": price if price is not None else "Not available"})
    return out


def main(date_str: str) -> Dict[str, Any]:
    """
    Основная функция, возвращающая словарь с данными для отображения.

    Args:
        date_str (str): дата и время в формате 'YYYY-MM-DD HH:MM:SS'.

    Returns:
        dict: структурированный ответ с приветствием, данными по картам, топ-транзакциям и т.д.
    """
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        logger.error(f"Invalid date format: {date_str}. Use 'YYYY-MM-DD HH:MM:SS'.")
        return {}

    greeting = get_greeting
