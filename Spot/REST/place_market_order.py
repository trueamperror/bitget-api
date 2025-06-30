#!/usr/bin/env python3
"""
Bitget API - Размещение Market ордера (Spot)
Рыночный ордер исполняется немедленно по текущей рыночной цене

Официальная документация:
https://www.bitget.com/api-doc/spot/trade/Place-Order

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
        url = f"{config['baseURL']}/api/v2/spot/market/tickers?symbol={symbol}"
        response = requests.get(url, timeout=config.get('timeout', 30))
        
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
        url = f"{config['baseURL']}/api/v2/spot/public/symbols"
        response = requests.get(url, timeout=config.get('timeout', 30))
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '00000' and data.get('data'):
                for symbol_info in data['data']:
                    if symbol_info.get('symbol') == symbol:
                        return {
                            'minTradeAmount': float(symbol_info.get('minTradeAmount', 0)),
                            'priceScale': int(symbol_info.get('priceScale', 4)),
                            'quantityScale': int(symbol_info.get('quantityScale', 6)),
                            'baseCoin': symbol_info.get('baseCoin'),
                            'quoteCoin': symbol_info.get('quoteCoin')
                        }
        return None
    except:
        return None

def place_market_order(config, symbol, side, quantity=None, quote_quantity=None):
    """
    Размещение market ордера
    
    Параметры:
    - symbol: Торговая пара (например, 'BTCUSDT')
    - side: 'buy' или 'sell'
    - quantity: Количество базовой валюты (для sell или buy по количеству)
    - quote_quantity: Количество котируемой валюты (для buy по сумме)
    """
    
    # Подготовка данных ордера
    order_data = {
        'symbol': symbol.upper(),
        'side': side.lower(),
        'orderType': 'market',
        'force': 'gtc'  # Good Till Cancel
    }
    
    # Для market ордера используем size (количество)
    if side.lower() == 'buy':
        if quote_quantity:
            # Покупка на определенную сумму USDT
            order_data['size'] = str(quote_quantity)
        else:
            print("❌ Для market buy ордера нужно указать quote_quantity (сумму в USDT)")
            return None
    else:
        if quantity:
            # Продажа определенного количества базовой валюты
            order_data['size'] = str(quantity)
        else:
            print("❌ Для market sell ордера нужно указать quantity (количество базовой валюты)")
            return None
    
    body = json.dumps(order_data)
    
    # Параметры для подписи
    timestamp = str(int(time.time() * 1000))
    method = 'POST'
    request_path = '/api/v2/spot/trade/place-order'
    query_string = ''
    
    # Создание подписи
    signature = create_signature(timestamp, method, request_path, query_string, body, config['secretKey'])
    
    # Заголовки запроса
    headers = {
        'ACCESS-KEY': config['apiKey'],
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': config['passphrase'],
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }
    
    # URL запроса
    url = f"{config['baseURL']}{request_path}"
    
    try:
        print(f"🔄 Размещение MARKET ордера...")
        print(f"💱 Пара: {symbol}")
        print(f"🎯 Сторона: {'🟢 ПОКУПКА' if side.lower() == 'buy' else '🔴 ПРОДАЖА'}")
        if side.lower() == 'buy' and quote_quantity:
            print(f"💰 Сумма: {quote_quantity} USDT")
        elif side.lower() == 'sell' and quantity:
            print(f"📏 Количество: {quantity}")
        
        response = requests.post(url, headers=headers, data=body, timeout=config.get('timeout', 30))
        
        # Сохранение примера ответа
        response_data = response.json() if response.status_code == 200 else {"error": response.text}
        save_response_example('place_market_order', {
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
            
    except requests.exceptions.Timeout:
        print("❌ Превышено время ожидания запроса")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return None
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return None

def save_response_example(endpoint_name, data):
    """Сохранение примера ответа в JSON файл"""
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
    
    print(f"\n✅ MARKET ОРДЕР РАЗМЕЩЕН!")
    print("=" * 40)
    
    order_id = order_result.get('orderId', 'N/A')
    client_order_id = order_result.get('clientOid', 'N/A')
    
    print(f"🆔 ID ордера: {order_id}")
    print(f"👤 Client ID: {client_order_id}")
    print(f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    
    print(f"\n💡 Market ордер должен исполниться немедленно!")
    print(f"📊 Проверьте результат:")
    print(f"   python Spot/REST/get_account_balance.py")
    print(f"   python Spot/REST/get_trades.py")

def main():
    """Основная функция"""
    print("⚡ РАЗМЕЩЕНИЕ MARKET ОРДЕРА BITGET SPOT")
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
    
    if current_price and current_price > 0:
        print(f"💰 Текущая цена: ${current_price:.4f}")
    
    if symbol_info:
        print(f"📏 Минимальная сумма: {symbol_info['minTradeAmount']}")
        print(f"🪙 Базовая валюта: {symbol_info['baseCoin']}")
        print(f"💵 Котируемая валюта: {symbol_info['quoteCoin']}")
    
    # Выбор стороны
    print(f"\n🎯 Выберите сторону:")
    print("1. 🟢 Покупка (BUY)")
    print("2. 🔴 Продажа (SELL)")
    
    side_choice = input("Ваш выбор (1-2): ").strip()
    
    if side_choice == "1":
        side = "buy"
        # Для покупки нужна сумма в USDT
        quote_quantity = input("💰 Введите сумму для покупки в USDT (минимум 5): ").strip()
        try:
            quote_quantity = float(quote_quantity)
            if quote_quantity < 5:
                print("❌ Минимальная сумма для покупки: 5 USDT")
                return
        except ValueError:
            print("❌ Неверный формат суммы")
            return
        
        quantity = None
        
    elif side_choice == "2":
        side = "sell"
        # Для продажи нужно количество базовой валюты
        quantity = input(f"📏 Введите количество {symbol_info['baseCoin'] if symbol_info else 'базовой валюты'} для продажи: ").strip()
        try:
            quantity = float(quantity)
            if symbol_info and quantity < symbol_info['minTradeAmount']:
                print(f"❌ Минимальное количество: {symbol_info['minTradeAmount']}")
                return
        except ValueError:
            print("❌ Неверный формат количества")
            return
        
        quote_quantity = None
        
    else:
        print("❌ Неверный выбор")
        return
    
    # Подтверждение
    print(f"\n❓ ПОДТВЕРЖДЕНИЕ MARKET ОРДЕРА")
    print("=" * 35)
    print(f"💱 Пара: {symbol}")
    print(f"🎯 Сторона: {'🟢 ПОКУПКА' if side == 'buy' else '🔴 ПРОДАЖА'}")
    if side == 'buy':
        print(f"💰 Сумма: {quote_quantity} USDT")
        if current_price and current_price > 0 and quote_quantity:
            estimated_qty = quote_quantity / current_price
            print(f"📊 Примерное количество: {estimated_qty:.6f}")
    else:
        print(f"📏 Количество: {quantity}")
        if current_price and current_price > 0 and quantity:
            estimated_value = quantity * current_price
            print(f"📊 Примерная стоимость: ${estimated_value:.2f}")
    
    print(f"\n⚠️ ВНИМАНИЕ: Market ордер исполнится НЕМЕДЛЕННО по рыночной цене!")
    confirm = input("✅ Подтвердите размещение ордера (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Размещение ордера отменено")
        return
    
    # Размещение ордера
    result = place_market_order(config, symbol, side, quantity, quote_quantity)
    
    if result:
        display_order_result(result)
    else:
        print("❌ Не удалось разместить market ордер")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
