#!/usr/bin/env python3
"""
Bitget USDT Perpetual REST API - Get Public Trades

Получение публичных сделок для фьючерсной торговой пары.
Показывает историю последних сделок на рынке фьючерсов.

Документация: https://www.bitget.com/api-doc/contract/market/Get-Recent-Fills

Параметры:
- symbol: торговая пара (обязательный)
- limit: количество записей (1-100, по умолчанию 100)
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


def get_futures_public_trades(symbol="BTCUSDT", limit=10):
    """
    Получение публичных сделок для фьючерсов
    
    Args:
        symbol (str): Торговая пара
        limit (int): Количество записей (1-100)
    
    Returns:
        dict: Ответ API с данными сделок
    """
    config = load_config()
    if not config:
        return None
    
    # Параметры запроса
    params = {
        'symbol': symbol,
        'productType': 'USDT-FUTURES',
        'limit': limit
    }
    
    try:
        url = f"{config['baseURL']}/api/v2/mix/market/fills"
        headers = {
            'Content-Type': 'application/json',
            'locale': 'en-US'
        }
        
        print(f"📊 Получение публичных сделок для {symbol} (FUTURES)...")
        
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
    result = get_futures_public_trades("BTCUSDT", limit=5)
    if result:
        print("\\n✅ Тест прошел успешно!")
    else:
        print("\\n❌ Тест не прошел!")
