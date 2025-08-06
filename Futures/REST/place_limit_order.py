#!/usr/bin/env python3
"""
Bitget Futures - Размещение лимитного ордера
Place Limit Order API

Документация: https://www.bitget.com/api-doc/contract/trade/Place-Order
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
endpoint = "/api/v2/mix/order/place-order"

timestamp = str(int(time.time() * 1000))

# Тело запроса
body = {
    "symbol": "DOGEUSDT",
    "productType": "USDT-FUTURES",
    "marginMode": "crossed",
    "marginCoin": "USDT",
    "size": "50",
    "side": "sell",
    "orderType": "limit",
    "price": "0.2020"
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

print(f"Размещение лимитного ордера:")
print(f"Символ: DOGEUSDT")
print(f"Сторона: sell")
print(f"Размер: 50")
print(f"Цена: 0.2020")
print(f"Тип: limit")
print("-" * 50)

# Отправка запроса
response = requests.post(
    base_url + endpoint,
    headers=headers,
    data=body_json
)

# Вывод результата
print(json.dumps(response.json(), indent=4, ensure_ascii=False))
