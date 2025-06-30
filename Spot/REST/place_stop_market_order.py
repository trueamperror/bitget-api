#!/usr/bin/env python3
"""
Размещение Stop Market ордера на Bitget Spot
Stop Market - ордер, который становится market ордером при достижении определенной цены
"""

import requests
import json
import hmac
import hashlib
import base64
import time
from datetime import datetime

def load_config():
    """Загрузка конфигурации"""
    with open('../../config.json', 'r') as f:
        return json.load(f)

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
    """Получение текущей цены"""
    try:
        url = f"{config['baseURL']}/api/v2/spot/market/tickers?symbol={symbol}"
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
        url = f"{config['baseURL']}/api/v2/spot/public/symbols"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '00000':
                for symbol_info in data['data']:
                    if symbol_info.get('symbol') == symbol:
                        return {
                            'minTradeAmount': float(symbol_info.get('minTradeAmount', 0)),
                            'priceScale': int(symbol_info.get('priceScale', 2)),
                            'quantityScale': int(symbol_info.get('quantityScale', 6)),
                            'baseCoin': symbol_info.get('baseCoin'),
                            'quoteCoin': symbol_info.get('quoteCoin')
                        }
        return None
    except Exception as e:
        print(f"❌ Ошибка получения информации о символе: {e}")
        return None

def save_response_example(endpoint_name, data):
    """Сохранение примера ответа"""
    try:
        filename = f"../../docs/response_examples/{endpoint_name}_{int(time.time())}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Пример ответа сохранен: {filename}")
    except Exception as e:
        print(f"⚠️ Не удалось сохранить пример ответа: {e}")

def place_stop_market_order(config, symbol, side, size, trigger_price):
    """
    Размещение Stop Market ордера
    
    Args:
        config: Конфигурация API
        symbol: Торговая пара (например, 'BTCUSDT')
        side: 'buy' или 'sell'
        size: Размер ордера (для buy - в quote валюте, для sell - в base валюте)
        trigger_price: Цена срабатывания stop ордера
    """
    
    # Подготовка данных ордера
    order_data = {
        'symbol': symbol.upper(),
        'side': side.lower(),
        'orderType': 'market',  # После срабатывания trigger стает market ордером
        'size': str(size),
        'triggerPrice': str(trigger_price),
        'triggerType': 'fill_price',  # Тип триггера по цене последней сделки
        'force': 'gtc'
    }
    
    body = json.dumps(order_data)
    timestamp = str(int(time.time() * 1000))
    method = 'POST'
    request_path = '/api/v2/spot/trade/place-plan-order'  # План-ордер для stop orders
    
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
        response = requests.post(url, headers=headers, data=body, timeout=30)
        
        # Сохраняем пример ответа
        response_data = response.json() if response.status_code == 200 else {"error": response.text}
        save_response_example('place_stop_market_order', {
            'request': order_data,
            'response': response_data,
            'status_code': response.status_code,
            'timestamp': datetime.now().isoformat()
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '00000':
                return data.get('data', {}), None
            else:
                return None, data.get('msg', 'Unknown error')
        else:
            return None, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return None, str(e)

def main():
    """Основная функция"""
    print("🔥 РАЗМЕЩЕНИЕ STOP MARKET ОРДЕРА")
    print("=" * 40)
    
    # Загрузка конфигурации
    config = load_config()
    
    # Параметры ордера (можно настроить через аргументы командной строки)
    symbol = "BTCUSDT"
    
    # Получение информации о символе и текущей цены
    symbol_info = get_symbol_info(config, symbol)
    current_price = get_current_price(config, symbol)
    
    if not current_price or not symbol_info:
        print("❌ Не удалось получить информацию о символе или цену")
        return
    
    print(f"💰 Текущая цена {symbol}: ${current_price:.2f}")
    print(f"📏 Точность цены: {symbol_info['priceScale']} знаков")
    
    # Пример для stop-loss sell (если цена упадет)
    # Trigger на 2% ниже текущей цены
    stop_loss_trigger = round(current_price * 0.98, symbol_info['priceScale'])
    size = round(1.1 / current_price, symbol_info['quantityScale'])  # Минимум 1.1 USDT
    
    print(f"📉 Stop Market Sell:")
    print(f"   Размер: {size} BTC")
    print(f"   Trigger Price: ${stop_loss_trigger}")
    print(f"   Сработает если цена упадет до ${stop_loss_trigger}")
    
    confirm = input("\n❓ Разместить stop market ордер? (y/N): ").strip().lower()
    
    if confirm == 'y':
        print("\n🔄 Размещение ордера...")
        
        result, error = place_stop_market_order(
            config=config,
            symbol=symbol,
            side='sell',
            size=size,
            trigger_price=stop_loss_trigger
        )
        
        if result:
            order_id = result.get('orderId', result.get('planOrderId'))
            print(f"✅ Stop Market ордер успешно размещен!")
            print(f"📋 Order ID: {order_id}")
            print(f"💰 Размер: {size}")
            print(f"🎯 Trigger Price: ${stop_loss_trigger}")
            print(f"⚠️  Ордер сработает автоматически при достижении trigger цены")
            
            # Вывод полного ответа для анализа
            print(f"\n📊 Полный ответ API:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ Ошибка размещения ордера: {error}")
    else:
        print("❌ Размещение ордера отменено")

if __name__ == "__main__":
    main()
