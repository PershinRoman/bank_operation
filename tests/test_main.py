import pytest
import pandas as pd
import datetime

from src.main import get_greeting, get_card_stats, get_top_transactions


def test_get_greeting_morning():
    time = datetime.time(6, 0)
    assert get_greeting(time) == 'Доброе утро'


def test_get_greeting_day():
    time = datetime.time(13, 0)
    assert get_greeting(time) == 'Добрый день'


def test_get_greeting_evening():
    time = datetime.time(19, 0)
    assert get_greeting(time) == 'Добрый вечер'


def test_get_greeting_night():
    time = datetime.time(2, 0)
    assert get_greeting(time) == 'Доброй ночи'


@pytest.fixture
def sample_df():
    data = {
        'Номер карты': [1234567890123456, 1234567890129999, 1234567890123456],
        'Сумма платежа': [1000, 2000, 300],
        'Дата операции': [
            '2023-10-01 12:00:00',
            '2023-10-02 12:00:00',
            '2023-10-05 12:00:00'
        ],
        'Описание': ['Тест 1', 'Тест 2', 'Тест 3']
    }
    df = pd.DataFrame(data)
    df['Дата операции'] = pd.to_datetime(df['Дата операции'])
    return df


def test_get_card_stats(sample_df):
    result = get_card_stats(sample_df)
    # Ожидаем, что у первой карты (последние 4 digits) '3456' сумма 1300 и кешбэк 13
    assert '3456' in result
    assert result['3456']['total_spent'] == 1300.0
    assert result['3456']['cashback'] == 13

    # Ожидаем, что у второй карты (последние 4 digits) '9999' сумма 2000 и кешбэк 20
    assert '9999' in result
    assert result['9999']['total_spent'] == 2000.0
    assert result['9999']['cashback'] == 20


def test_get_top_transactions(sample_df):
    result = get_top_transactions(sample_df)
    # Ожидаем 2-3 транзакции или до 5 (в данном случае 3)
    assert len(result) == 3
    # Первая транзакция должна быть с суммой 2000
    assert result[0]['Сумма платежа'] == 2000
