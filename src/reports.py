import pandas as pd
import datetime


"""Функция расчёта трат по категор"""


def spending_by_category(transactions, category, date=None):
    if date is None:
        date = pd.to_datetime('today')
    else:
        date = pd.to_datetime(date)

    # Определяем дату три месяца назад
    date_3_months_ago = date - pd.DateOffset(months=3)

    # Фильтруем данные по дате и категории
    transactions['Дата операции'] = pd.to_datetime(transactions['Дата операции'])
    filtered_transactions = transactions[
        (transactions['Дата операции'] >= date_3_months_ago) &
        (transactions['Дата операции'] <= date) &
        (transactions['Категория'] == category)
    ]

    # Группируем по месяцу и суммируем суммы операций
    filtered_transactions['Месяц'] = filtered_transactions['Дата операции'].dt.to_period('M')
    monthly_spending = filtered_transactions.groupby('Месяц')['Сумма платежа'].sum()

    return monthly_spending.round(2)


# Считываем данные
df = pd.read_excel('data/operations.xls')

# Рассчитываем траты по категории 'Продукты' за последние три месяца
category_spending = spending_by_category(df, 'Продукты')

# Выводим результат
print(category_spending)


def save_report(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        filename = f"{func.__name__}_report_{datetime.datetime.now().strftime('%Y-%m-%d')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(str(result))
        return result
    return wrapper
