import pandas as pd
import datetime
import json
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


"""функция для определения приветсвия"""


def get_greeting(date_str):
    time = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').time()
    if datetime.time(5, 0) <= time < datetime.time(12, 0):
        return 'Доброе утро'
    elif datetime.time(12, 0) <= time < datetime.time(17, 0):
        return 'Добрый день'
    elif datetime.time(17, 0) <= time < datetime.time(23, 0):
        return 'Добрый вечер'
    else:
        return 'Доброй ночи'


"""функция для обработки данных по картам"""


def get_card_info(df):
    card_info = {}
    grouped = df.groupby('Номер карты')
    for card_number, group in grouped:
        last_four_digits = str(card_number)[-4:]
        total_spent = group['Сумма платежа'].sum()
        cashback = int(total_spent // 100)
        card_info[last_four_digits] = {
            'total_spent': round(total_spent, 2),
            'cashback': cashback
        }
    return card_info


"""tоп 5 транзакций"""


def get_top_transactions(df):
    top_transactions = df.nlargest(5, 'Сумма платежа')[['Дата операции', 'Описание', 'Сумма платежа']]
    return top_transactions.to_dict(orient='records')


"""Функции для получения курса валют и стоимости акций"""


def get_currency_rates(currencies):
    rates = {}
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/RUB')
        data = response.json()
        for currency in currencies:
            rates[currency] = data['rates'].get(currency, 'Not available')
    except Exception as e:
        logger.error(f"Error fetching currency rates: {e}")
    return rates


"""стоимость акций"""


def get_stock_prices(stocks):
    stock_prices = {}
    api_key = 'K9HVA34Q6Q2XJC6K'
    for stock in stocks:
        try:
            response = requests.get(f'https://www.alphavantage.co/query', params={
                'function': 'GLOBAL_QUOTE',
                'symbol': stock,
                'apikey': api_key
            })
            data = response.json()
            price = data['Global Quote']['05. price']
            stock_prices[stock] = price
        except Exception as e:
            logger.error(f"Error fetching stock price for {stock}: {e}")
            stock_prices[stock] = 'Not available'
    return stock_prices


def main(date_str):
    # Получаем приветствие
    greeting = get_greeting(date_str)

    # Считываем данные
    df = pd.read_excel('data/operations.xls')

    # Приводим даты к нужному формату
    df['Дата операции'] = pd.to_datetime(df['Дата операции'])

    # Фильтруем данные с начала месяца до указанной даты
    date = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    start_month = date.replace(day=1)
    df_filtered = df[
        (df['Дата операции'] >= start_month) & (df['Дата операции'] <= date)
    ]

    # Получаем информацию по картам
    card_info = get_card_info(df_filtered)

    # Получаем топ-5 транзакций
    top_transactions = get_top_transactions(df_filtered)

    # Получаем пользовательские настройки
    with open('user_settings.json', 'r') as f:
        user_settings = json.load(f)

    # Получаем курсы валют
    currency_rates = get_currency_rates(user_settings['user_currencies'])

    # Получаем стоимость акций
    stock_prices = get_stock_prices(user_settings['user_stocks'])

    # Формируем ответ
    response = {
        'greeting': greeting,
        'cards': card_info,
        'top_transactions': top_transactions,
        'currency_rates': currency_rates,
        'stock_prices': stock_prices
    }

    # Возвращаем JSON-ответ
    return json.dumps(response, ensure_ascii=False)


if __name__ == '__main__':
    date_input = '2023-10-20 14:30:00'
    result = main(date_input)
    print(result)
