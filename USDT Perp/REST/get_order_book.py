#!/usr/bin/env python3
"""
Bitget USDT Perpetual REST API - Get Order Book

Получение стакана заявок (книга ордеров) для фьючерсной торговой пары.
Показывает текущие bid/ask заявки в стакане фьючерсов.

Документация: https://www.bitget.com/api-doc/contract/market/Get-Merge-Depth

Параметры:
- symbol: торговая пара (обязательный)
- precision: точность цены (по умолчанию 0.0001)
- limit: количество уровней (5, 15, 50, 100, по умолчанию 50)
"""

import requests
import json
from datetime import datetime


def load_config():
    """Загрузка конфигурации из файла"""
    try:
        with open('/Users/timurbogatyrev/Documents/VS Code/Algo/ExchangeAPI/Bitget/config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл config.json не найден!")
        return None


def get_futures_order_book(symbol="BTCUSDT", precision="0.1", limit=50):
    """
    Получение стакана заявок для фьючерсного контракта
    
    Args:
        symbol (str): Торговая пара
        precision (str): Точность цены
        limit (int): Количество уровней (5, 15, 50, 100)
    
    Returns:
        dict: Данные стакана заявок
    """
    
    config = load_config()
    if not config:
        return None
    
    # Проверяем корректность лимита
    if limit not in [5, 15, 50, 100]:
        print(f"⚠️ Некорректный лимит {limit}, используем 50")
        limit = 50
    
    # Параметры запроса
    params = {
        'symbol': symbol,
        'productType': 'USDT-FUTURES',
        'limit': limit
    }
    
    try:
        # Отправляем запрос
        url = f"{config['baseURL']}/api/v2/mix/market/merge-depth"
        headers = {
            'Content-Type': 'application/json',
            'locale': 'en-US'
        }
        
        print(f"📚 Получение стакана заявок для {symbol} (FUTURES)...")
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Запрос выполнен успешно")
            print("📋 RAW JSON Response от биржи:")
            print("=" * 50)
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("=" * 50)
            
            return data
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return None
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return None


if __name__ == "__main__":
    # Тестируем функцию
    result = get_futures_order_book("BTCUSDT", limit=5)
    if result:
        print("\\n✅ Тест прошел успешно!")
    else:
        print("\\n❌ Тест не прошел!")
