#!/usr/bin/env python3
"""
Bitget API - Получение баланса аккаунта (USDT Perpetual Futures)
Получение информации о балансе и доступных средствах для торговли фьючерсами

Официальная документация:
https://www.bitget.com/api-doc/contract/account/Get-Account-Information

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
from pathlib import Path

def load_config():
    """Загрузка конфигурации из файла"""
    try:
        config_path = Path(__file__).parent.parent.parent / "config.json"
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл config.json не найден!")
        print("📝 Создайте файл config.json с вашими API ключами")
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

def get_account_balance(config, product_type='USDT-FUTURES'):
    """Получение баланса фьючерсного аккаунта"""
    
    # Параметры запроса
    params = {
        'productType': product_type
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    timestamp = str(int(time.time() * 1000))
    method = 'GET'
    request_path = '/api/v2/mix/account/accounts'
    body = ''
    
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
    url = f"{config['baseURL']}{request_path}?{query_string}"
    
    try:
        print("🚀 Bitget USDT Perpetual Futures - Account Balance")
        print("=" * 55)
        print("🔄 Получение информации о балансе...")
        print(f"🌐 Эндпоинт: {request_path}")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        # Сохранение примера ответа
        response_data = response.json() if response.status_code == 200 else {"error": response.text}
        save_response_example('futures_account_balance', {
            'request': {
                'method': method,
                'url': request_path,
                'params': params
            },
            'response': response_data,
            'status_code': response.status_code,
            'timestamp': datetime.now().isoformat()
        })
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Запрос выполнен успешно")
            print("📋 RAW JSON Response от биржи:")
            print("=" * 50)
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("=" * 50)
            
            return data
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
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

def display_account_info(account_data):
    """Отображение информации о балансе"""
    
    if not account_data:
        print("❌ Нет данных о балансе")
        return
    
    print(f"\n💰 ИНФОРМАЦИЯ О БАЛАНСЕ FUTURES АККАУНТА")
    print("=" * 60)
    
    # Если есть несколько аккаунтов (для разных валют)
    for account in account_data:
        margin_coin = account.get('marginCoin', 'N/A')
        
        print(f"\n🪙 Валюта маржи: {margin_coin}")
        print("-" * 40)
        
        # Основные балансы
        locked = float(account.get('locked', 0))
        available = float(account.get('available', 0))
        cross_max_available = float(account.get('crossMaxAvailable', 0))
        fixed_max_available = float(account.get('fixedMaxAvailable', 0))
        max_transfer_out = float(account.get('maxTransferOut', 0))
        equity = float(account.get('equity', 0))
        usd_tvalue = float(account.get('usdtTotalAmount', 0))
        
        print(f"💳 Общий капитал: {equity:.4f} {margin_coin}")
        print(f"💰 Доступно: {available:.4f} {margin_coin}")
        print(f"🔒 Заблокировано: {locked:.4f} {margin_coin}")
        print(f"📊 В USD эквиваленте: ${usd_tvalue:.2f}")
        
        print(f"\n📈 ТОРГОВЫЕ ЛИМИТЫ:")
        print("-" * 30)
        print(f"🔄 Кросс-маржа (макс. доступно): {cross_max_available:.4f} {margin_coin}")
        print(f"🎯 Изолированная маржа (макс. доступно): {fixed_max_available:.4f} {margin_coin}")
        print(f"📤 Максимум для вывода: {max_transfer_out:.4f} {margin_coin}")
        
        # Дополнительные поля если есть
        unrealized_pl = account.get('unrealizedPL')
        if unrealized_pl is not None:
            unrealized_pl = float(unrealized_pl)
            print(f"💹 Нереализованная P&L: {unrealized_pl:.4f} {margin_coin}")
        
        bonus = account.get('bonus')
        if bonus is not None:
            bonus = float(bonus)
            print(f"🎁 Бонус: {bonus:.4f} {margin_coin}")
        
        # Информация о позициях
        cross_risk_rate = account.get('crossRiskRate')
        if cross_risk_rate is not None:
            risk_rate = float(cross_risk_rate)
            print(f"⚠️ Уровень риска (кросс): {risk_rate:.2%}")
    
    print(f"\n💡 ПОДСКАЗКИ:")
    print("-" * 20)
    print("🔍 Для просмотра открытых позиций: python get_positions.py")
    print("📊 Для просмотра открытых ордеров: python get_open_orders.py")
    print("💱 Для размещения ордера: python place_order.py")

def main():
    """Основная функция"""
    
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
    
    print("🔑 API ключи загружены успешно")
    
    # Получение баланса
    balance_data = get_account_balance(config)
    
    if balance_data:
        print(f"\n✅ Баланс получен успешно!")
        
        # Опциональный выбор валюты для детального просмотра
        print(f"\n🔍 Хотите посмотреть детали по конкретной валюте?")
        for i, account in enumerate(balance_data):
            margin_coin = account.get('marginCoin', 'N/A')
            available = float(account.get('available', 0))
            print(f"{i+1}. {margin_coin} (доступно: {available:.4f})")
        
        print("✅ Баланс получен успешно!")
    else:
        print("❌ Не удалось получить информацию о балансе")

if __name__ == "__main__":
    main()
