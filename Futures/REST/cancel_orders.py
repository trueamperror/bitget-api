#!/usr/bin/env python3
"""
Bitget Futures - Отмена ордера
Cancel Order API

Документация: https://www.bitget.com/api-doc/contract/trade/Cancel-Order
"""

import json
import hmac
import hashlib
import base64
import time
import requests
from datetime import datetime
from pathlib import Path

config_path = Path(__file__).parent.parent.parent / "config.json"
with open(config_path, 'r') as file:
    config = json.load(file)

base_url = "https://api.bitget.com"
endpoint = "/api/v2/mix/order/cancel-order"

timestamp = str(int(time.time() * 1000))

# Тело запроса - параметры для отмены ордера
body = {
    "symbol": "DOGEUSDT",
    "productType": "USDT-FUTURES",
    "marginCoin": "USDT",
    "orderId": "1336229587700531565"  # ID ордера для отмены
}

body_json = json.dumps(body)

# Создание подписи
if "":
    message = f"{timestamp}POST{endpoint}?{body_json}"
else:
    message = f"{timestamp}POST{endpoint}{body_json}"

signature = hmac.new(
    config['secretKey'].encode('utf-8'),
    message.encode('utf-8'),
    hashlib.sha256
).digest()

signature = base64.b64encode(signature).decode('utf-8')

# Заголовки
headers = {
    'ACCESS-KEY': config['apiKey'],
    'ACCESS-SIGN': signature,
    'ACCESS-TIMESTAMP': timestamp,
    'ACCESS-PASSPHRASE': config['passphrase'],
    'Content-Type': 'application/json',
    'locale': 'en-US'
}

print(f"Отмена ордера:")
print(f"Символ: {body['symbol']}")
print(f"ID ордера: {body['orderId']}")
print(f"Продукт: {body['productType']}")
print("-" * 50)

# Отправка запроса
response = requests.post(
    base_url + endpoint,
    headers=headers,
    data=body_json
)

# Вывод результата
print(json.dumps(response.json(), indent=4, ensure_ascii=False))
