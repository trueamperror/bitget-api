#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures - Get Symbol Info
Документация: https://www.bitget.com/api-doc/contract/market/Get-Symbol-Information
"""

import requests
import json
import os
from datetime import datetime

# Параметры запроса
FUTURES_PARAMS = {
    'productType': 'USDT-FUTURES'
}

# Путь для сохранения ответа
RESPONSE_DIR = os.path.join(os.path.dirname(__file__), '../../docs/response examples/Futures')
os.makedirs(RESPONSE_DIR, exist_ok=True)

config_path = os.path.join(os.path.dirname(__file__), '../../config.json')

try:
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
except Exception as e:
    print(f"Error loading config: {e}")
    exit(1)

BASE_URL = config.get('baseURL', 'https://api.bitget.com')

def get_symbol_info():
    endpoint = f"{BASE_URL}/api/v2/mix/market/contracts"
    
    try:
        response = requests.get(endpoint, params=FUTURES_PARAMS, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"HTTP Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"Request error: {e}")
        return None

def main():
    result = get_symbol_info()
    
    if result:
        # Сохраняем в файл
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"futures_symbols_{timestamp}.json"
        filepath = os.path.join(RESPONSE_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Futures symbols saved to: {filepath}")
        print(f"Total symbols: {len(result.get('data', []))}")
        
        # Также выводим JSON в консоль
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Failed to get symbol info")

if __name__ == "__main__":
    main()
