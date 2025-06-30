#!/usr/bin/env python3
"""
Bitget USDT Perpetual REST API - Set Margin Mode

Установка режима маржи (cross/isolated) для торговой пары.

Документация: https://www.bitget.com/api-doc/contract/account/Change-Margin-Mode
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


def generate_signature(timestamp, method, request_path, query_string='', body=''):
    """Генерация подписи для аутентификации"""
    config = load_config()
    if not config:
        return None
    
    if query_string:
        message = f"{timestamp}{method.upper()}{request_path}?{query_string}{body}"
    else:
        message = f"{timestamp}{method.upper()}{request_path}{body}"
    
    signature = hmac.new(
        config['secretKey'].encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    return base64.b64encode(signature).decode('utf-8')


def set_margin_mode(symbol, margin_mode):
    """
    Установка режима маржи для торговой пары
    
    Args:
        symbol (str): Торговая пара (например, BTCUSDT)
        margin_mode (str): Режим маржи (crossed/isolated)
    
    Returns:
        dict: Ответ API
    """
    config = load_config()
    if not config:
        return None
    
    # Подготавливаем данные запроса
    timestamp = str(int(time.time() * 1000))
    method = 'POST'
    request_path = '/api/v2/mix/account/set-margin-mode'
    
    body_data = {
        'symbol': symbol,
        'marginMode': margin_mode,
        'productType': 'USDT-FUTURES',
        'marginCoin': 'USDT'
    }
    
    body = json.dumps(body_data)
    
    # Генерируем подпись
    signature = generate_signature(timestamp, method, request_path, '', body)
    if not signature:
        return None
    
    # Заголовки
    headers = {
        'ACCESS-KEY': config['apiKey'],
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': config['passphrase'],
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }
    
    try:
        url = f"{config['baseURL']}{request_path}"
        
        print(f"💰 Установка режима маржи для {symbol}...")
        print(f"⚙️ Режим маржи: {margin_mode}")
        
        response = requests.post(url, headers=headers, data=body)
        
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
    # Тестируем с безопасными настройками
    result = set_margin_mode("BTCUSDT", "crossed")
    if result:
        print("\\n✅ Тест прошел успешно!")
    else:
        print("\\n❌ Тест не прошел!")
