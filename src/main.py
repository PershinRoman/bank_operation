import json
import logging
import datetime
import pandas as pd

from src.utils import read_excel_data, fetch_data_from_api

logger = logging.getLogger(__name__)


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


def main(date_str: str) -> dict:
    """
    Основная функция приложения (пример для страницы «Главная»).
    Принимает дату в формате 'YYYY-MM-DD HH:MM:SS'.
    Возвращает словарь (который можно сериализовать в JSON)
    с приветствием и статистикой по транзакциям.
    """
    # Преобразуем входную строку в datetime
    try:
        input_date = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        logger.error(f"Invalid date format: {date_str}, should be YYYY-MM-DD HH:MM:SS.")
        # Возвращаем пустой результат или делаем raise — по выбору
        return {}

    # Приветствие
    greeting = get_greeting(input_date.time())

    # Считываем данные
    df = read_excel_data('data/operations.xls')

    # Фильтруем данные c начала месяца до указанной даты
    start_of_month = input_date.replace(day=1, hour=0, minute=0, second=0)
    mask = (df['Дата операции'] >= start_of_month) & (df['Дата операции'] <= input_date)
    df_filtered = df[mask]

    # Считаем расходы по каждой карте
    cards_info = get_card_stats(df_filtered)

    # Топ-5 транзакций
    top_5 = get_top_transactions(df_filtered)

    # Загружаем настройки
    user_settings = load_user_settings('user_settings.json')

    # Получаем курсы валют
    rates = get_currency_rates(user_settings.get('user_currencies', []))

    # Получаем стоимость акций
    stocks = get_stock_prices(user_settings.get('user_stocks', []))

    # Финальный результат
    data_output = {
        'greeting': greeting,
        'cards': cards_info,
        'top_transactions': top_5,
        'currency_rates': rates,
        'stock_prices': stocks
    }
    return data_output


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


def get_card_stats(df: pd.DataFrame) -> dict:
    """
    Группирует суммы платежей по номеру карты и считает кэшбэк (1 рубль на каждые 100 рублей).
    """
    card_info = {}
    grouped = df.groupby('Номер карты')['Сумма платежа'].sum()
    for card_number, total_spent in grouped.items():
        last4 = str(card_number)[-4:]
        cashback = int(total_spent // 100)
        card_info[last4] = {
            'total_spent': float(round(total_spent, 2)),
            'cashback': cashback
        }
    return card_info


def get_top_transactions(df: pd.DataFrame) -> list:
    """
    Возвращает список (до 5) самых больших по сумме платежа транзакций.
    """
    top_df = df.nlargest(5, 'Сумма платежа')
    # Можно оставить только нужные поля
    result = top_df[['Дата операции', 'Описание', 'Сумма платежа']].to_dict(orient='records')
    return result


def get_currency_rates(currencies: list) -> dict:
    """
    Получает курсы указанных валют по отношению к рублю.
    """
    if not currencies:
        return {}
    url = "https://api.exchangerate-api.com/v4/latest/RUB"
    data = fetch_data_from_api(url)
    if not data:
        return {}

    rates = {}
    # В случае успеха ожидаем структуру { 'rates': { 'USD': ..., 'EUR': ... } }
    all_rates = data.get('rates', {})
    for c in currencies:
        rates[c] = all_rates.get(c, 'Not available')
    return rates


def get_stock_prices(stocks: list) -> dict:
    """
    Получает текущие цены акций, например, используя Alpha Vantage или любой другой API.
    """
    if not stocks:
        return {}
    api_key = "YOUR_API_KEY"  # Подставьте свой ключ или используйте другой сервис
    results = {}
    base_url = "https://www.alphavantage.co/query"
    for symbol in stocks:
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': api_key
        }
        data = fetch_data_from_api(base_url, params=params)
        # Обрабатываем ответ
        try:
            price = data['Global Quote']['05. price']
            results[symbol] = price
        except KeyError:
            logger.error(f"Could not find price info for {symbol}")
            results[symbol] = 'Not available'
    return results


if __name__ == '__main__':
    # Пример вызова
    input_date_str = '2023-10-23 14:30:00'
    result_data = main(input_date_str)
    print(result_data)
