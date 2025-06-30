#!/usr/bin/env python3
"""
Bitget USDT Perpetual REST API - Get Margin Information

Получение информации о марже и настройках позиций для USDT Perpetual Futures.

Документация: https://www.bitget.com/api-doc/contract/account/Get-Account-Information

Параметры:
- symbol: торговая пара (опциональный)
- productType: тип продукта (по умолчанию USDT-FUTURES)
"""

import requests
import json
import hmac
import hashlib
import base64
import time
from datetime import datetime


def load_config():
    """Загрузка конфигурации из файла"""
    try:
        with open('/Users/timurbogatyrev/Documents/VS Code/Algo/ExchangeAPI/Bitget/config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл config.json не найден!")
        return None


def create_signature(timestamp, method, request_path, query_string, body, secret_key):
    """Создание подписи для аутентификации"""
    if query_string:
        message = f"{timestamp}{method.upper()}{request_path}?{query_string}{body}"
    else:
        message = f"{timestamp}{method.upper()}{request_path}{body}"
    
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    return base64.b64encode(signature).decode('utf-8')


def get_margin_info(symbol="BTCUSDT"):
    """
    Получение информации о марже для торговой пары
    
    Args:
        symbol (str): Торговая пара
    
    Returns:
        dict: Ответ API с информацией о марже
    """
    config = load_config()
    if not config:
        return None
    
    # Параметры запроса
    params = {
        'productType': 'USDT-FUTURES'
    }
    
    try:
        timestamp = str(int(time.time() * 1000))
        method = 'GET'
        request_path = '/api/v2/mix/account/accounts'
        
        # Формируем query string
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        
        # Создаем подпись
        signature = create_signature(timestamp, method, request_path, query_string, '', config['secretKey'])
        
        headers = {
            'ACCESS-KEY': config['apiKey'],
            'ACCESS-SIGN': signature,
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-PASSPHRASE': config['passphrase'],
            'Content-Type': 'application/json',
            'locale': 'en-US'
        }
        
        url = f"{config['baseURL']}{request_path}?{query_string}"
        
        print(f"📊 Получение информации о марже для {symbol}...")
        
        response = requests.get(url, headers=headers, timeout=30)
        
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
    result = get_margin_info("BTCUSDT")
    if result:
        print("\\n✅ Тест прошел успешно!")
    else:
        print("\\n❌ Тест не прошел!")
