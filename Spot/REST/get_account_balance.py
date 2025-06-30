# -*- coding: utf-8 -*-
"""
Bitget Spot REST API - Get Account Balance
Получение баланса спот аккаунта

Документация: https://www.bitget.com/api-doc/spot/account/Get-Account-Assets

Описание:
Этот скрипт получает баланс всех активов на спот аккаунте Bitget.
Требует API ключи с правами на чтение аккаунта.

Параметры:
- coin: конкретная валюта (опционально, если не указано - все валюты)

Возвращаемые данные:
- coin: название валюты
- available: доступный баланс
- frozen: замороженный баланс
- locked: заблокированный баланс
- uTime: время последнего обновления
"""

import requests
import json
import hmac
import hashlib
import base64
import time
import os
from datetime import datetime

# Определение пути к файлу конфигурации
config_path = os.path.join(os.path.dirname(__file__), '../../config.json')

# Загрузка конфигурации
try:
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
except Exception as e:
    print(f"❌ Ошибка загрузки конфигурации: {e}")
    exit(1)

# Настройки API
API_KEY = config.get('apiKey', '')
SECRET_KEY = config.get('secretKey', '')
PASSPHRASE = config.get('passphrase', '')
BASE_URL = config.get('baseURL', 'https://api.bitget.com')

def create_signature(timestamp, method, request_path, query_string, body):
    """
    Создание подписи для Bitget API
    
    Args:
        timestamp (str): Временная метка в миллисекундах
        method (str): HTTP метод (GET, POST, etc.)
        request_path (str): Путь запроса
        query_string (str): Строка запроса (параметры после ?)
        body (str): Тело запроса
    
    Returns:
        str: Base64 подпись
    """
    
    # Формируем строку для подписи согласно документации Bitget
    if query_string:
        message = f"{timestamp}{method.upper()}{request_path}?{query_string}{body}"
    else:
        message = f"{timestamp}{method.upper()}{request_path}{body}"
    
    # Создаем HMAC-SHA256 подпись
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    # Кодируем в base64
    return base64.b64encode(signature).decode('utf-8')

def get_account_balance(coin=None):
    """
    Получение баланса аккаунта
    
    Args:
        coin (str): Конкретная валюта (опционально)
    
    Returns:
        list: Список балансов или None при ошибке
    """
    
    # Проверяем наличие API ключей
    if not API_KEY or not SECRET_KEY or not PASSPHRASE:
        print("❌ API ключи не настроены в конфигурации")
        print("💡 Убедитесь, что в config.json заполнены:")
        print("   - apiKey")
        print("   - secretKey") 
        print("   - passphrase")
        return None
    
    # Формируем путь запроса
    request_path = "/api/v2/spot/account/assets"
    
    # Параметры запроса
    params = {}
    if coin:
        params['coin'] = coin
    
    # Формируем строку запроса
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()]) if params else ""
    
    # Подготовка для подписи
    timestamp = str(int(time.time() * 1000))
    method = "GET"
    body = ""
    
    # Создаем подпись
    signature = create_signature(timestamp, method, request_path, query_string, body)
    
    # Заголовки
    headers = {
        'ACCESS-KEY': API_KEY,
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }
    
    # Формируем полный URL
    url = f"{BASE_URL}{request_path}"
    if query_string:
        url += f"?{query_string}"
    
    try:
        print(f"💰 Запрос баланса аккаунта...")
        if coin:
            print(f"🪙 Валюта: {coin}")
        else:
            print(f"🪙 Все валюты")
        
        # Выполняем запрос
        response = requests.get(url, headers=headers, timeout=10)
        
        # Проверяем статус ответа
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем код ответа Bitget
            if data.get('code') == '00000':
                balance_data = data.get('data', [])
                if balance_data:
                    print(f"✅ Получен баланс по {len(balance_data)} валютам")
                    return balance_data
                else:
                    print("⚠️ Баланс пуст или не найден")
                    return []
            else:
                print(f"❌ Ошибка API Bitget: {data.get('msg', 'Неизвестная ошибка')}")
                return None
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return None
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return None

def format_balance_response(balance_data):
    """
    Форматирование ответа с балансом
    
    Args:
        balance_data (list): Данные баланса
    """
    
    if not balance_data:
        print("💰 Баланс пуст или не найден")
        return
    
    print(f"\\n💰 БАЛАНС SPOT АККАУНТА BITGET")
    print("=" * 80)
    print(f"🔢 Всего валют: {len(balance_data)}")
    
    # Заголовок таблицы
    print(f"\\n{'Валюта':^10} {'Доступно':>15} {'Заморожено':>15} {'Заблокировано':>15} {'Общий баланс':>15}")
    print("-" * 80)
    
    total_balances = []
    non_zero_balances = []
    
    for balance in balance_data:
        try:
            coin = balance.get('coin', 'N/A')
            available = float(balance.get('available', 0))
            frozen = float(balance.get('frozen', 0))
            locked = float(balance.get('locked', 0))
            update_time = balance.get('uTime', '')
            
            total = available + frozen + locked
            
            total_balances.append({
                'coin': coin,
                'available': available,
                'frozen': frozen,
                'locked': locked,
                'total': total,
                'update_time': update_time
            })
            
            # Сохраняем только ненулевые балансы для отображения
            if total > 0:
                non_zero_balances.append({
                    'coin': coin,
                    'available': available,
                    'frozen': frozen,
                    'locked': locked,
                    'total': total,
                    'update_time': update_time
                })
                
        except (ValueError, KeyError) as e:
            print(f"❌ Ошибка обработки баланса: {e}")
            continue
    
    # Сортируем по общему балансу
    non_zero_balances.sort(key=lambda x: x['total'], reverse=True)
    
    # Показываем ненулевые балансы
    for balance in non_zero_balances:
        coin = balance['coin']
        available = balance['available']
        frozen = balance['frozen']
        locked = balance['locked']
        total = balance['total']
        
        print(f"{coin:^10} {available:>15.6f} {frozen:>15.6f} {locked:>15.6f} {total:>15.6f}")
    
    # Статистика
    print(f"\\n📊 СТАТИСТИКА БАЛАНСА:")
    print("-" * 40)
    print(f"💰 Всего валют: {len(total_balances)}")
    print(f"💰 Валют с балансом > 0: {len(non_zero_balances)}")
    print(f"💰 Пустых балансов: {len(total_balances) - len(non_zero_balances)}")
    
    if non_zero_balances:
        # Топ валют по балансу
        print(f"\\n🏆 ТОП ВАЛЮТ ПО БАЛАНСУ:")
        print("-" * 30)
        
        for i, balance in enumerate(non_zero_balances[:10], 1):
            coin = balance['coin']
            total = balance['total']
            available_percent = (balance['available'] / total * 100) if total > 0 else 0
            
            print(f"{i:2d}. {coin}: {total:.6f} (доступно: {available_percent:.1f}%)")
        
        # Анализ заморозки средств
        frozen_balances = [b for b in non_zero_balances if b['frozen'] > 0]
        locked_balances = [b for b in non_zero_balances if b['locked'] > 0]
        
        if frozen_balances:
            print(f"\\n🧊 ЗАМОРОЖЕННЫЕ СРЕДСТВА:")
            print("-" * 30)
            for balance in frozen_balances[:5]:
                coin = balance['coin']
                frozen = balance['frozen']
                total = balance['total']
                frozen_percent = (frozen / total * 100) if total > 0 else 0
                print(f"🧊 {coin}: {frozen:.6f} ({frozen_percent:.1f}% от общего)")
        
        if locked_balances:
            print(f"\\n🔒 ЗАБЛОКИРОВАННЫЕ СРЕДСТВА:")
            print("-" * 30)
            for balance in locked_balances[:5]:
                coin = balance['coin']
                locked = balance['locked']
                total = balance['total']
                locked_percent = (locked / total * 100) if total > 0 else 0
                print(f"🔒 {coin}: {locked:.6f} ({locked_percent:.1f}% от общего)")
        
        # Анализ ликвидности
        total_available = sum(b['available'] for b in non_zero_balances)
        total_frozen = sum(b['frozen'] for b in non_zero_balances)
        total_locked = sum(b['locked'] for b in non_zero_balances)
        grand_total = total_available + total_frozen + total_locked
        
        if grand_total > 0:
            print(f"\\n💧 АНАЛИЗ ЛИКВИДНОСТИ:")
            print("-" * 30)
            print(f"💧 Доступно: {total_available/grand_total*100:.1f}%")
            print(f"🧊 Заморожено: {total_frozen/grand_total*100:.1f}%")
            print(f"🔒 Заблокировано: {total_locked/grand_total*100:.1f}%")

def check_specific_balance(coin):
    """
    Проверка баланса конкретной валюты
    
    Args:
        coin (str): Символ валюты
    
    Returns:
        dict: Баланс валюты или None
    """
    
    balances = get_account_balance(coin)
    
    if balances and len(balances) > 0:
        return balances[0]
    
    return None

def main():
    """Основная функция"""
    print("💰 Bitget Spot REST API - Get Account Balance")
    print("=" * 55)
    
    # Получаем баланс всех валют
    balances = get_account_balance()
    
    # Выводим сырой JSON ответ
    if balances is not None:
        import json
        print("\n📄 RAW JSON RESPONSE:")
        print(json.dumps(balances, indent=2, ensure_ascii=False))
        
        # Также форматируем и выводим результат
        format_balance_response(balances)
        
        # Демонстрация проверки конкретной валюты
        print(f"\\n🔍 ДЕМОНСТРАЦИЯ ПРОВЕРКИ КОНКРЕТНОЙ ВАЛЮТЫ:")
        print("-" * 50)
        
        test_coins = ['USDT', 'BTC', 'ETH']
        for coin in test_coins:
            balance = check_specific_balance(coin)
            if balance:
                available = float(balance.get('available', 0))
                total = available + float(balance.get('frozen', 0)) + float(balance.get('locked', 0))
                print(f"💰 {coin}: {total:.6f} (доступно: {available:.6f})")
            else:
                print(f"💰 {coin}: Нет баланса или ошибка")
        
        # Важная информация о безопасности
        print(f"\\n🔐 ИНФОРМАЦИЯ О БЕЗОПАСНОСТИ:")
        print("-" * 40)
        print("⚠️  Этот скрипт использует реальные API ключи")
        print("🔒 Убедитесь, что API ключи имеют только необходимые права")
        print("📱 Рекомендуется использовать IP whitelist в настройках API")
        print("🕐 API ключи должны иметь ограниченное время жизни")
        
    else:
        print("❌ Не удалось получить баланс аккаунта")
        print("\\n🔍 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
        print("- Неверные API ключи в config.json")
        print("- API ключи не имеют прав на чтение аккаунта")
        print("- Проблемы с сетевым подключением")
        print("- API ключи заблокированы или истекли")

if __name__ == "__main__":
    main()
