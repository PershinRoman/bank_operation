import pandas as pd
import datetime
import json


"""Функция анализа категорий кешбэка"""


def analyze_cashback_categories(data, year, month):
    # Фильтруем данные за указанный месяц и год
    data['Дата операции'] = pd.to_datetime(data['Дата операции'])
    data_filtered = data[(data['Дата операции'].dt.year == year) & (data['Дата операции'].dt.month == month)]

    # Группируем по категориям и суммируем суммы операций
    category_sums = data_filtered.groupby('Категория')['Сумма платежа'].sum()

    # Рассчитываем потенциальный кешбэк (например, 5% от суммы расходов)
    cashback_percent = 0.05
    cashback_potential = category_sums * cashback_percent

    # Преобразуем в словарь
    cashback_dict = cashback_potential.round(2).to_dict()

    return cashback_dict


# Считываем данные
df = pd.read_excel('data/operations.xlsx')

# Анализируем кешбэк за сентябрь 2023 года
cashback_analysis = analyze_cashback_categories(df, 2023, 9)

# Выводим результат
print(json.dumps(cashback_analysis, ensure_ascii=False))


"""Функция для расчёта суммы инвесткопилки"""


def investment_bank(month, transactions, limit):
    # Преобразуем строку месяца в дату
    month_date = datetime.datetime.strptime(month, '%Y-%m')
    year = month_date.year
    month = month_date.month

    # Фильтруем транзакции за указанный месяц и год
    transactions['Дата операции'] = pd.to_datetime(transactions['Дата операции'])
    data_filtered = transactions[(transactions['Дата операции'].dt.year == year) & (transactions['Дата операции'].dt.month == month)]

    # Рассчитываем сумму для инвесткопилки
    total_investment = 0
    for amount in data_filtered['Сумма операции']:
        # Для расходов
        if amount < 0:
            # Модуль суммы
            abs_amount = abs(amount)
            # Округляем вверх до ближайшего шага
            rounding = (limit - abs_amount % limit) % limit
            total_investment += rounding

    return round(total_investment, 2)


# Считываем данные
df = pd.read_excel('data/operations.xlsx')

# Рассчитываем сумму инвесткопилки за октябрь 2023 года с шагом округления 50 рублей
investment_sum = investment_bank('2023-10', df, 50)

# Выводим результат
print(f"Сумма, отложенная в Инвесткопилку: {investment_sum} рублей")
