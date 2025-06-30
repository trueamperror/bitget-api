#!/usr/bin/env python3
"""
Отмена план-ордера (stop/take profit orders) Bitget Spot
"""

import requests
import json
import hmac
import hashlib
import base64
import time
import sys

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

def cancel_plan_order(config, symbol, order_id):
    """Отмена план-ордера"""
    order_data = {
        'symbol': symbol.upper(),
        'orderId': str(order_id)
    }
    
    body = json.dumps(order_data)
    timestamp = str(int(time.time() * 1000))
    method = 'POST'
    request_path = '/api/v2/spot/trade/cancel-plan-order'
    
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
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '00000':
                return True, data.get('msg', 'Success')
            else:
                return False, data.get('msg', 'Unknown error')
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, str(e)

def main():
    if len(sys.argv) != 3:
        print("Использование: python cancel_plan_order.py <order_id> <symbol>")
        print("Пример: python cancel_plan_order.py 1323411432578789376 BTCUSDT")
        return
    
    order_id = sys.argv[1]
    symbol = sys.argv[2]
    
    print(f"🗑️ ОТМЕНА ПЛАН-ОРДЕРА")
    print("=" * 40)
    print(f"📋 Order ID: {order_id}")
    print(f"💱 Symbol: {symbol}")
    
    config = load_config()
    
    print(f"\n🔄 Отмена план-ордера...")
    success, msg = cancel_plan_order(config, symbol, order_id)
    
    if success:
        print(f"✅ План-ордер успешно отменен!")
        print(f"📝 Ответ: {msg}")
    else:
        print(f"❌ Ошибка отмены план-ордера: {msg}")

if __name__ == "__main__":
    main()
