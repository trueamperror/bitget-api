#!/usr/bin/env python3
"""
Bitget USDT Perpetual REST API - Get Leverage Information

Получение информации о доступных уровнях плеча для торговых пар.
Показывает детальную информацию о плече в зависимости от размера позиции.

Документация: https://www.bitget.com/api-doc/contract/market/Get-Position-Tier

Параметры:
- symbol: торговая пара (обязательный)
- productType: тип продукта (по умолчанию USDT-FUTURES)
"""

import requests
import json
import time
from datetime import datetime


def get_leverage_info(symbol="BTCUSDT", productType="USDT-FUTURES"):
    """
    Получить информацию о доступных уровнях плеча для торговой пары.
    
    Args:
        symbol (str): Торговая пара (например, "BTCUSDT")
        productType (str): Тип продукта ("USDT-FUTURES", "COIN-FUTURES", "SUSDT-FUTURES", "SCOIN-FUTURES")
    
    Returns:
        dict: Ответ API с данными о плече или None при ошибке
    """
    
    endpoint = "/api/v2/mix/market/query-position-lever"
    base_url = "https://api.bitget.com"
    url = base_url + endpoint
    
    # Параметры запроса
    params = {
        'symbol': symbol,
        'productType': productType
    }
    
    try:
        print(f"📡 Запрос информации о плече для {symbol}...")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        print(f"🌐 URL: {response.url}")
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Запрос выполнен успешно")
            print("📋 RAW JSON Response от биржи:")
            print("=" * 50)
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("=" * 50)
            
            return data
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 Ответ сервера: {error_data}")
            except:
                print(f"📝 Ответ сервера: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Превышено время ожидания запроса")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к API")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return None
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return None


def interactive_mode():
    """Интерактивный режим для тестирования API."""
    print("🚀 Интерактивный режим получения информации о плече")
    print("=" * 60)
    
    while True:
        print("\n📋 Опции:")
        print("1. Получить плечо для BTCUSDT")
        print("2. Получить плечо для ETHUSDT")
        print("3. Получить плечо для ADAUSDT")
        print("4. Ввести свой символ")
        print("5. Выход")
        
        choice = input("\n💫 Выберите опцию (1-5): ").strip()
        
        if choice == '1':
            get_leverage_info("BTCUSDT")
        elif choice == '2':
            get_leverage_info("ETHUSDT")
        elif choice == '3':
            get_leverage_info("ADAUSDT")
        elif choice == '4':
            symbol = input("💰 Введите символ (например, SOLUSDT): ").strip().upper()
            if symbol:
                get_leverage_info(symbol)
            else:
                print("❌ Символ не может быть пустым")
        elif choice == '5':
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор")


if __name__ == "__main__":
    interactive_mode()
