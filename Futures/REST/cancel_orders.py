#!/usr/bin/env python3
"""
ТЕСТИРОВАНИЕ: Получение открытых ордеров на USDT Perpetual Futures на Bitget
"""

import json
import hmac
import hashlib
import base64
import time
import requests
from datetime import datetime


def load_config():
    """Загрузка конфигурации из файла"""
    try:
        with open('../../config.json', 'r') as f:
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


def make_authenticated_request(config, method, endpoint, params=None):
    """Выполнение аутентифицированного запроса"""
    timestamp = str(int(time.time() * 1000))
    query_string = ''
    body = ''
    
    if method.upper() == 'GET' and params:
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    elif method.upper() == 'POST' and params:
        body = json.dumps(params)
    
    signature = create_signature(timestamp, method, endpoint, query_string, body, config['secretKey'])
    
    headers = {
        'ACCESS-KEY': config['apiKey'],
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': config['passphrase'],
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }
    
    url = f"{config['baseURL']}{endpoint}"
    if query_string:
        url += f"?{query_string}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        else:
            response = requests.post(url, headers=headers, data=body, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return None


def save_response_example(endpoint_name, data):
    """Сохранение примера ответа"""
    try:
        filename = f"../../docs/{endpoint_name}_response.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Пример ответа сохранен: {filename}")
    except Exception as e:
        print(f"⚠️ Не удалось сохранить пример: {e}")


def main():
    """Основная функция"""
    print("📊 ТЕСТИРОВАНИЕ: Получение открытых ордеров BITGET FUTURES")
    print("=" * 60)
    
    # Загрузка конфигурации
    config = load_config()
    if not config:
        return
    
    # Проверка API ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase', 'baseURL']
    for key in required_keys:
        if not config.get(key):
            print(f"❌ Отсутствует ключ '{key}' в config.json")
            return
    
    # Тестируем получение открытых ордеров
    print("🔄 Получение всех открытых futures ордеров...")
    response = make_authenticated_request(config, 'GET', '/api/v2/mix/order/orders-pending', 
                                        {'productType': 'USDT-FUTURES'})
    
    if response:
        print("\n📋 RAW JSON RESPONSE:")
        print("=" * 50)
        print(json.dumps(response, indent=2, ensure_ascii=False))
        print("=" * 50)
        
        # Сохраняем пример ответа
        save_response_example('get_open_orders', response)
        
        # Показываем краткую статистику
        if response.get('code') == '00000':
            data = response.get('data', {})
            orders = data.get('entrustedList', []) if isinstance(data, dict) else []
            print(f"\n📊 СТАТИСТИКА:")
            print(f"✅ Всего открытых ордеров: {len(orders)}")
            
            if orders and len(orders) > 0:
                symbols = []
                for order in orders:
                    if isinstance(order, dict) and 'symbol' in order:
                        symbols.append(order['symbol'])
                
                if symbols:
                    unique_symbols = set(symbols)
                    print(f"💱 Уникальных символов: {len(unique_symbols)}")
                    print(f"🔗 Символы: {', '.join(sorted(unique_symbols))}")
                
                # Показываем детали ордеров
                print(f"\n📋 ДЕТАЛИ ОРДЕРОВ:")
                for i, order in enumerate(orders[:5], 1):  # Показываем первые 5
                    if isinstance(order, dict):
                        symbol = order.get('symbol', 'N/A')
                        side = order.get('side', 'N/A')
                        size = order.get('size', 'N/A')
                        price = order.get('price', 'N/A')
                        order_type = order.get('orderType', 'N/A')
                        print(f"   {i}. {symbol} {side.upper()} {size} @ ${price} ({order_type})")
                
                if len(orders) > 5:
                    print(f"   ... и еще {len(orders) - 5} ордеров")
            else:
                print("📝 Открытых ордеров нет")
        else:
            print(f"❌ Ошибка API: {response.get('msg')}")
    else:
        print("❌ Не удалось получить данные")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
