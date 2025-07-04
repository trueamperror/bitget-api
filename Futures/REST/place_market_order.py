#!/usr/bin/env python3
"""
Bitget API - Размещение Market ордера (USDT Perpetual Futures)
Рыночный ордер исполняется немедленно по текущей рыночной цене

Официальная документация:
https://www.bitget.com/api-doc/contract/trade/Place-Order

Требует аутентификации: Да
Лимит запросов: 10 запросов/секунду
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
        with open('../../config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл config.json не найден!")
        return None
    except json.JSONDecodeError:
        print("❌ Ошибка в формате файла config.json!")
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

def get_current_price(config, symbol):
    """Получение текущей цены для информации"""
    try:
        url = f"{config['baseURL']}/api/v2/mix/market/ticker?symbol={symbol}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '00000' and data.get('data'):
                ticker_data = data['data'][0] if isinstance(data['data'], list) else data['data']
                return float(ticker_data.get('lastPr', 0))
        return None
    except:
        return None

def get_symbol_info(config, symbol):
    """Получение информации о торговой паре"""
    try:
        url = f"{config['baseURL']}/api/v2/mix/market/contracts"
        params = {'productType': 'USDT-FUTURES'}
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '00000' and data.get('data'):
                for symbol_info in data['data']:
                    if symbol_info.get('symbol') == symbol:
                        return {
                            'minTradeNum': float(symbol_info.get('minTradeNum', 0)),
                            'priceEndStep': float(symbol_info.get('priceEndStep', 0)),
                            'volumePlace': int(symbol_info.get('volumePlace', 0)),
                            'pricePlace': int(symbol_info.get('pricePlace', 0)),
                            'baseCoin': symbol_info.get('baseCoin'),
                            'quoteCoin': symbol_info.get('quoteCoin'),
                            'maxLever': symbol_info.get('maxLever'),
                            'minLever': symbol_info.get('minLever')
                        }
        return None
    except:
        return None

def place_market_order(config, symbol, side, size, margin_mode='crossed'):
    """
    Размещение market ордера на фьючерсах (One-way mode)
    
    Параметры:
    - symbol: Торговая пара (например, 'BTCUSDT')
    - side: 'buy' (длинная позиция) или 'sell' (короткая позиция)
    - size: Размер позиции в контрактах
    - margin_mode: 'crossed' (кросс-маржа) или 'isolated' (изолированная маржа)
    """
    
    # Подготовка данных ордера (One-way mode)
    order_data = {
        'symbol': symbol.upper(),
        'productType': 'USDT-FUTURES',
        'marginMode': margin_mode,
        'marginCoin': 'USDT',
        'size': str(size),
        'side': side.lower(),
        'orderType': 'market',
        'force': 'ioc'  # Immediate or Cancel для market ордеров
    }
    
    body = json.dumps(order_data)
    timestamp = str(int(time.time() * 1000))
    method = 'POST'
    request_path = '/api/v2/mix/order/place-order'
    
    signature = create_signature(timestamp, method, request_path, '', body, config['secretKey'])
    
    headers = {
        'ACCESS-KEY': config['apiKey'],
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': config['passphrase'],
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }
    
    url = f"{config['baseURL']}{request_path}"
    
    try:
        print(f"🔄 Размещение FUTURES MARKET ордера...")
        print(f"💱 Пара: {symbol}")
        print(f"🎯 Сторона: {get_side_emoji(side)} {side.upper()}")
        print(f"📏 Размер: {size} контрактов")
        print(f"⚖️ Режим маржи: {margin_mode}")
        
        response = requests.post(url, headers=headers, data=body, timeout=30)
        
        # Сохранение примера ответа
        response_data = response.json() if response.status_code == 200 else {"error": response.text}
        save_response_example('place_futures_market_order', {
            'request': order_data,
            'response': response_data,
            'status_code': response.status_code,
            'timestamp': datetime.now().isoformat()
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '00000':
                return data.get('data', {})
            else:
                print(f"❌ Ошибка API: {data.get('msg')}")
                return None
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def get_side_emoji(side):
    """Получение эмодзи для стороны ордера"""
    side_emojis = {
        'buy': '🟢',
        'sell': '�'
    }
    return side_emojis.get(side.lower(), '⚪')

def save_response_example(endpoint_name, data):
    """Сохранение примера ответа"""
    try:
        filename = f"../../docs/response_examples/{endpoint_name}_{int(time.time())}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Пример ответа сохранен: {filename}")
    except Exception as e:
        print(f"⚠️ Не удалось сохранить пример ответа: {e}")

def display_order_result(order_result):
    """Отображение результата размещения ордера"""
    if not order_result:
        return
    
    print(f"\n✅ FUTURES MARKET ОРДЕР РАЗМЕЩЕН!")
    print("=" * 45)
    
    order_id = order_result.get('orderId', 'N/A')
    client_order_id = order_result.get('clientOid', 'N/A')
    
    print(f"🆔 ID ордера: {order_id}")
    print(f"👤 Client ID: {client_order_id}")
    print(f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    
    print(f"\n💡 Market ордер должен исполниться немедленно!")
    print(f"📊 Проверьте результат:")
    print(f"   python get_positions.py")
    print(f"   python get_account_balance.py")

def main():
    """Основная функция"""
    print("⚡ РАЗМЕЩЕНИЕ FUTURES MARKET ОРДЕРА BITGET")
    print("=" * 50)
    
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
    
    # Выбор торговой пары
    symbol = input("💱 Введите символ пары (по умолчанию BTCUSDT): ").strip().upper()
    if not symbol:
        symbol = "BTCUSDT"
    
    # Получение информации о паре
    print(f"🔄 Получение информации о {symbol}...")
    symbol_info = get_symbol_info(config, symbol)
    current_price = get_current_price(config, symbol)
    
    if current_price:
        print(f"💰 Текущая цена: ${current_price:.4f}")
    
    if symbol_info:
        print(f"📏 Минимальный размер: {symbol_info['minTradeNum']}")
        print(f"🪙 Базовая валюта: {symbol_info['baseCoin']}")
        print(f"💵 Котируемая валюта: {symbol_info['quoteCoin']}")
        print(f"🔢 Максимальное плечо: {symbol_info['maxLever']}")
    
    # Выбор стороны
    print(f"\n🎯 Выберите действие:")
    print("1. 🟢 Купить (Buy) - Длинная позиция")
    print("2. 🔴 Продать (Sell) - Короткая позиция")
    
    side_choice = input("Ваш выбор (1-2): ").strip()
    
    side_map = {
        "1": "buy",
        "2": "sell"
    }
    
    if side_choice not in side_map:
        print("❌ Неверный выбор")
        return
    
    side = side_map[side_choice]
    
    # Размер позиции
    size = input("📏 Введите размер позиции в контрактах: ").strip()
    try:
        size = float(size)
        if symbol_info and size < symbol_info['minTradeNum']:
            print(f"❌ Минимальный размер: {symbol_info['minTradeNum']}")
            return
    except ValueError:
        print("❌ Неверный формат размера")
        return
    
    # Выбор режима маржи
    print(f"\n⚖️ Выберите режим маржи:")
    print("1. 🔄 Кросс-маржа (Crossed) - Рекомендуется")
    print("2. 🎯 Изолированная маржа (Isolated)")
    
    margin_choice = input("Ваш выбор (1-2): ").strip()
    
    if margin_choice == "1":
        margin_mode = "crossed"
    elif margin_choice == "2":
        margin_mode = "isolated"
    else:
        print("❌ Неверный выбор")
        return
    
    # Подтверждение
    print(f"\n❓ ПОДТВЕРЖДЕНИЕ FUTURES MARKET ОРДЕРА")
    print("=" * 45)
    print(f"💱 Пара: {symbol}")
    print(f"🎯 Действие: {get_side_emoji(side)} {side.upper()}")
    print(f"📏 Размер: {size} контрактов")
    print(f"⚖️ Режим маржи: {margin_mode}")
    
    if current_price and current_price > 0:
        notional_value = size * current_price
        print(f"📊 Примерная стоимость позиции: ${notional_value:.2f}")
    
    print(f"\n⚠️ ВНИМАНИЕ: Market ордер исполнится НЕМЕДЛЕННО по рыночной цене!")
    confirm = input("✅ Подтвердите размещение ордера (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Размещение ордера отменено")
        return
    
    # Размещение ордера
    result = place_market_order(config, symbol, side, size, margin_mode)
    
    if result:
        display_order_result(result)
    else:
        print("❌ Не удалось разместить futures market ордер")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
