#!/usr/bin/env python3
"""
Bitget Futures - Отмена плановой стоп-заявки
Cancel Plan Order API

Документация: https://www.bitget.com/api-doc/contract/plan/Cancel-Plan-Order
"""

import json
import requests
import time
import hmac
import base64
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent.parent.parent / "config.json"
    with open(config_path, 'r') as file:
        return json.load(file)

def create_signature(secret_key, timestamp, method, request_path, body=''):
    message = str(timestamp) + method.upper() + request_path + body
    signature = base64.b64encode(
        hmac.new(secret_key.encode(), message.encode(), digestmod='sha256').digest()
    ).decode()
    return signature

def cancel_plan_order():
    config = load_config()
    
    base_url = "https://api.bitget.com"
    endpoint = "/api/v2/mix/order/cancel-plan-order"
    
    timestamp = str(int(time.time() * 1000))
    
    # Тело запроса с хардкодными параметрами
    body = {
        "orderIdList": [
            {
                "orderId": "1336240979397656576"
            }
        ],
        "symbol": "DOGEUSDT",
        "productType": "USDT-FUTURES",
        "marginCoin": "USDT",
        "planType": "normal_plan"
    }
    
    body_json = json.dumps(body)
    
    # Создание подписи
    signature = create_signature(
        config['secretKey'],
        timestamp,
        'POST',
        endpoint,
        body_json
    )
    
    # Заголовки
    headers = {
        'ACCESS-KEY': config['apiKey'],
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': config['passphrase'],
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }
    
    print(f"Отмена плановой стоп-заявки:")
    print(f"Символ: DOGEUSDT")
    print(f"Order ID: 1336239936371236864")
    print("-" * 50)
    
    # Отправка запроса
    response = requests.post(
        base_url + endpoint,
        headers=headers,
        data=body_json
    )
    
    # Вывод результата
    print(json.dumps(response.json(), indent=4, ensure_ascii=False))

if __name__ == "__main__":
    cancel_plan_order()
