#!/usr/bin/env python3
import requests
import json
import hmac
import hashlib
import base64
import time
import os

# =============================================================================
# ПАРАМЕТРЫ ЗАПРОСА - РЕДАКТИРУЙ ЗДЕСЬ
# =============================================================================
SYMBOL = "DOGEUSDT"
PRODUCT_TYPE = "USDT-FUTURES"
MARGIN_COIN = "USDT"
# =============================================================================

def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "..", "..", "config.json")
    config_path = os.path.normpath(config_path)
    with open(config_path, "r") as f:
        return json.load(f)

def create_signature(timestamp, method, request_path, body, secret_key):
    message = str(timestamp) + method + request_path + body
    signature = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()

def main():
    config = load_config()
    
    timestamp = str(int(time.time() * 1000))
    method = "GET"
    request_path = "/api/v2/mix/account/account"
    
    params = {
        "symbol": SYMBOL,
        "productType": PRODUCT_TYPE,
        "marginCoin": MARGIN_COIN
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_path = f"{request_path}?{query_string}"
    
    signature = create_signature(timestamp, method, full_path, "", config["secretKey"])
    
    headers = {
        "ACCESS-KEY": config["apiKey"],
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": config["passphrase"],
        "Content-Type": "application/json"
    }
    
    url = config["baseURL"] + full_path
    response = requests.get(url, headers=headers)
    
    print(json.dumps(response.json(), indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()
