import logging
from typing import Dict, Any
import requests
import pandas as pd

"""Инициализация логирования"""
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def read_excel_data(filepath: str) -> pd.DataFrame:
    """
    Считывает данные из Excel-файла и приводит столбец 'Дата операции' к формату datetime.
    """
    try:
        df = pd.read_excel(filepath)
        # Приведение дат к правильному формату
        df['Дата операции'] = pd.to_datetime(df['Дата операции'])
        logger.info(f"Successfully read data from {filepath}")
        return df
    except FileNotFoundError:
        logger.error(f"File {filepath} not found.")
        raise
    except Exception as e:
        logger.error(f"Error reading Excel file {filepath}: {e}")
        raise


def fetch_data_from_api(url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Выполняет GET-запрос к API и возвращает JSON-данные.
    Оборачиваем запрос в try-except, чтобы избежать падения при ошибках сети.
    """
    if params is None:
        params = {}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched data from {url}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from {url}: {e}")
        return {}
