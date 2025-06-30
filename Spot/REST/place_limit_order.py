#!/usr/bin/env python3
"""
Bitget API - Размещение Limit ордера (Spot)
Лимитный ордер размещается в стакане и ожидает исполнения по указанной цене

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
        print("❌ Файл ../../config.json не найден!")
        return None
    except json.JSONDecodeError:
        print("❌ Ошибка в формате файла ../../config.json!")
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

def get_order_book(config, symbol, limit=5):
    """Получение стакана заявок для анализа цен"""
    try:
        url = f"{config['baseURL']}/api/v2/spot/market/orderbook?symbol={symbol}&limit={limit}"
        response = requests.get(url, timeout=config.get('timeout', 30))
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '00000' and data.get('data'):
                return data['data']
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

def place_limit_order(config, symbol, side, quantity, price):
    """
    Размещение limit ордера
    
    Параметры:
    - symbol: Торговая пара (например, 'BTCUSDT')
    - side: 'buy' или 'sell'
    - quantity: Количество базовой валюты
    - price: Цена за единицу
    """
    
    # Подготовка данных ордера
    order_data = {
        'symbol': symbol.upper(),
        'side': side.lower(),
        'orderType': 'limit',
        'force': 'gtc',  # Good Till Cancel
        'size': str(quantity),
        'price': str(price)
    }
    
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
        print(f"🔄 Размещение LIMIT ордера...")
        print(f"💱 Пара: {symbol}")
        print(f"🎯 Сторона: {'🟢 ПОКУПКА' if side.lower() == 'buy' else '🔴 ПРОДАЖА'}")
        print(f"💰 Цена: ${price}")
        print(f"📏 Количество: {quantity}")
        print(f"💵 Общая стоимость: ${float(quantity) * float(price):.2f}")
        
        response = requests.post(url, headers=headers, data=body, timeout=config.get('timeout', 30))
        
        # Сохранение примера ответа
        response_data = response.json() if response.status_code == 200 else {"error": response.text}
        save_response_example('place_limit_order', {
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

def display_order_book_info(order_book, side):
    """Отображение информации из стакана для выбора цены"""
    if not order_book:
        return
    
    bids = order_book.get('bids', [])
    asks = order_book.get('asks', [])
    
    print(f"\n📚 СТАКАН ЗАЯВОК (топ-5)")
    print("=" * 40)
    
    if side.lower() == 'buy' and asks:
        print("🔴 ПРОДАЖИ (ASK) - цены для покупки:")
        for i, ask in enumerate(asks[:5], 1):
            price, volume = ask[0], ask[1]
            print(f"   {i}. ${float(price):.4f} ({float(volume):.4f})")
        
        best_ask = float(asks[0][0])
        suggested_price = best_ask * 0.99  # На 1% ниже лучшего ask
        print(f"\n💡 Рекомендуемая цена покупки: ${suggested_price:.4f} (на 1% ниже рынка)")
        return suggested_price
        
    elif side.lower() == 'sell' and bids:
        print("🟢 ПОКУПКИ (BID) - цены для продажи:")
        for i, bid in enumerate(bids[:5], 1):
            price, volume = bid[0], bid[1]
            print(f"   {i}. ${float(price):.4f} ({float(volume):.4f})")
        
        best_bid = float(bids[0][0])
        suggested_price = best_bid * 1.01  # На 1% выше лучшего bid
        print(f"\n💡 Рекомендуемая цена продажи: ${suggested_price:.4f} (на 1% выше рынка)")
        return suggested_price
    
    return None

def display_order_result(order_result):
    """Отображение результата размещения ордера"""
    if not order_result:
        return
    
    print(f"\n✅ LIMIT ОРДЕР РАЗМЕЩЕН!")
    print("=" * 40)
    
    order_id = order_result.get('orderId', 'N/A')
    client_order_id = order_result.get('clientOid', 'N/A')
    
    print(f"🆔 ID ордера: {order_id}")
    print(f"👤 Client ID: {client_order_id}")
    print(f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    
    print(f"\n📋 Limit ордер размещен в стакане и ожидает исполнения")
    print(f"🔍 Проверить статус:")
    print(f"   python Spot/REST/get_open_orders.py")
    print(f"   python Spot/REST/get_orders.py")

def main():
    """Основная функция"""
    print("📊 РАЗМЕЩЕНИЕ LIMIT ОРДЕРА BITGET SPOT")
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
        print(f"🎯 Точность цены: {symbol_info['priceScale']} знаков")
        print(f"📊 Точность количества: {symbol_info['quantityScale']} знаков")
    
    # Выбор стороны
    print(f"\n🎯 Выберите сторону:")
    print("1. 🟢 Покупка (BUY)")
    print("2. 🔴 Продажа (SELL)")
    
    side_choice = input("Ваш выбор (1-2): ").strip()
    
    if side_choice == "1":
        side = "buy"
    elif side_choice == "2":
        side = "sell"
    else:
        print("❌ Неверный выбор")
        return
    
    # Получение стакана заявок для анализа
    print(f"🔄 Получение стакана заявок...")
    order_book = get_order_book(config, symbol)
    suggested_price = display_order_book_info(order_book, side)
    
    # Ввод цены
    if suggested_price:
        price_input = input(f"💰 Введите цену (рекомендуемая ${suggested_price:.4f}): ").strip()
        if not price_input:
            price = suggested_price
        else:
            try:
                price = float(price_input)
            except ValueError:
                print("❌ Неверный формат цены")
                return
    else:
        price_input = input("💰 Введите цену: ").strip()
        try:
            price = float(price_input)
        except ValueError:
            print("❌ Неверный формат цены")
            return
    
    # Ввод количества
    if symbol_info:
        min_qty = symbol_info['minTradeAmount']
        quantity_input = input(f"📏 Введите количество (минимум {min_qty}): ").strip()
    else:
        quantity_input = input("📏 Введите количество: ").strip()
    
    try:
        quantity = float(quantity_input)
        if symbol_info and quantity < symbol_info['minTradeAmount']:
            print(f"❌ Минимальное количество: {symbol_info['minTradeAmount']}")
            return
    except ValueError:
        print("❌ Неверный формат количества")
        return
    
    # Анализ цены относительно рынка
    if current_price and current_price > 0:
        price_diff_pct = ((price - current_price) / current_price) * 100
        if side == 'buy':
            if price_diff_pct > 5:
                print(f"⚠️ Внимание: цена покупки на {price_diff_pct:.2f}% выше рынка")
            elif price_diff_pct < -10:
                print(f"💡 Хорошо: цена покупки на {abs(price_diff_pct):.2f}% ниже рынка")
        else:
            if price_diff_pct < -5:
                print(f"⚠️ Внимание: цена продажи на {abs(price_diff_pct):.2f}% ниже рынка")
            elif price_diff_pct > 10:
                print(f"💡 Хорошо: цена продажи на {price_diff_pct:.2f}% выше рынка")
    
    # Подтверждение
    total_value = quantity * price
    print(f"\n❓ ПОДТВЕРЖДЕНИЕ LIMIT ОРДЕРА")
    print("=" * 35)
    print(f"💱 Пара: {symbol}")
    print(f"🎯 Сторона: {'🟢 ПОКУПКА' if side == 'buy' else '🔴 ПРОДАЖА'}")
    print(f"💰 Цена: ${price:.4f}")
    print(f"📏 Количество: {quantity}")
    print(f"💵 Общая стоимость: ${total_value:.2f}")
    
    if current_price and current_price > 0:
        print(f"📊 Текущая рыночная цена: ${current_price:.4f}")
    
    print(f"\n💡 Limit ордер будет ожидать исполнения в стакане")
    confirm = input("✅ Подтвердите размещение ордера (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Размещение ордера отменено")
        return
    
    # Размещение ордера
    result = place_limit_order(config, symbol, side, quantity, price)
    
    if result:
        display_order_result(result)
    else:
        print("❌ Не удалось разместить limit ордер")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
