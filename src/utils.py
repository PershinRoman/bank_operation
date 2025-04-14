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
    try:
        df = pd.read_excel(filepath)
        return df
    except Exception as e:
        logger.error(f"Error reading Excel file {filepath}: {e}")
        return pd.DataFrame()  # возвращаем пустой DataFrame при ошибке


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
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching data from API {url}: {e}")
        return {}
