#!/usr/bin/env python3
"""
Bitget Spot REST API - Batch Cancel Orders

Отмена всех ордеров для торговой пары или всех ордеров аккаунта.
Поддерживает отмену по символу и типу ордера.

Документация: https://www.bitget.com/api-doc/spot/trade/Batch-Cancel-Order

Параметры:
- symbol: торговая пара (опционально, если не указан - отменяются все ордера)
"""

import requests
import json
import hmac
import hashlib
import base64
import time
from datetime import datetime


def load_config():
    """Загрузка конфигурации из файла"""
    try:
        with open('/Users/timurbogatyrev/Documents/VS Code/Algo/ExchangeAPI/Bitget/config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл config.json не найден!")
        return None


def generate_signature(timestamp, method, request_path, query_string='', body=''):
    """Генерация подписи для аутентификации"""
    config = load_config()
    if not config:
        return None
    
    if query_string:
        message = f"{timestamp}{method.upper()}{request_path}?{query_string}{body}"
    else:
        message = f"{timestamp}{method.upper()}{request_path}{body}"
    
    signature = hmac.new(
        config['secretKey'].encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    return base64.b64encode(signature).decode('utf-8')


def batch_cancel_orders(symbol=None):
    """
    Отмена всех ордеров
    
    Args:
        symbol (str, optional): Торговая пара (если не указан, отменяются все ордера)
    
    Returns:
        dict: Ответ API с результатом отмены
    """
    config = load_config()
    if not config:
        return None
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return None
    
    # Подготавливаем данные запроса
    timestamp = str(int(time.time() * 1000))
    method = 'POST'
    request_path = '/api/v2/spot/trade/cancel-batch-orders'
    
    # Формируем тело запроса
    body_data = {}
    if symbol:
        body_data['symbol'] = symbol
    
    body = json.dumps(body_data) if body_data else ''
    
    # Генерируем подпись
    signature = generate_signature(timestamp, method, request_path, '', body)
    if not signature:
        return None
    
    # Заголовки
    headers = {
        'ACCESS-KEY': config['apiKey'],
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': config['passphrase'],
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }
    
    try:
        url = f"{config['baseURL']}{request_path}"
        
        if symbol:
            print(f"🗑️ Отмена всех ордеров для {symbol}...")
        else:
            print("🗑️ Отмена ВСЕХ ордеров аккаунта...")
            print("⚠️ ВНИМАНИЕ: Будут отменены ВСЕ открытые ордера!")
        
        response = requests.post(url, headers=headers, data=body)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == '00000':
                result_data = data.get('data', {})
                
                print("✅ Пакетная отмена ордеров выполнена!")
                print("=" * 50)
                
                # Анализируем результат
                success_list = result_data.get('successList', [])
                failure_list = result_data.get('failureList', [])
                
                print(f"✅ Успешно отменено: {len(success_list)} ордеров")
                print(f"❌ Ошибки отмены: {len(failure_list)} ордеров")
                
                # Показываем успешно отмененные ордера
                if success_list:
                    print(f"\\n✅ УСПЕШНО ОТМЕНЕННЫЕ ОРДЕРА:")
                    print(f"{'Order ID':^20} {'Client OID':^15} {'Символ':^12}")
                    print("-" * 50)
                    
                    for order in success_list:
                        order_id = order.get('orderId', 'N/A')
                        client_oid = order.get('clientOid', 'N/A')
                        order_symbol = order.get('symbol', 'N/A')
                        
                        # Сокращаем длинные ID
                        short_order_id = order_id[-8:] if len(order_id) > 8 else order_id
                        short_client_oid = client_oid[-8:] if len(client_oid) > 8 else client_oid
                        
                        print(f"{short_order_id:^20} {short_client_oid:^15} {order_symbol:^12}")
                
                # Показываем ордера с ошибками
                if failure_list:
                    print(f"\\n❌ ОРДЕРА С ОШИБКАМИ:")
                    print(f"{'Order ID':^15} {'Client OID':^15} {'Ошибка':^25}")
                    print("-" * 60)
                    
                    for error in failure_list:
                        order_id = error.get('orderId', 'N/A')
                        client_oid = error.get('clientOid', 'N/A')
                        error_msg = error.get('errorMsg', 'Unknown error')
                        
                        # Сокращаем для отображения
                        short_order_id = order_id[-8:] if len(order_id) > 8 else order_id
                        short_client_oid = client_oid[-8:] if len(client_oid) > 8 else client_oid
                        short_error = error_msg[:23] + "..." if len(error_msg) > 25 else error_msg
                        
                        print(f"{short_order_id:^15} {short_client_oid:^15} {short_error:^25}")
                
                if not success_list and not failure_list:
                    print("ℹ️ Открытых ордеров для отмены не найдено")
                
                return data
            else:
                print(f"❌ Ошибка API: {data.get('msg', 'Unknown error')}")
                return None
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return None
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return None


def cancel_all_orders_interactive():
    """Интерактивная отмена ордеров с подтверждением"""
    print("🗑️ ПАКЕТНАЯ ОТМЕНА ОРДЕРОВ")
    print("=" * 40)
    
    print("⚠️ ВНИМАНИЕ: Эта операция отменит ордера!")
    print("\\n📝 Выберите режим отмены:")
    print("1. 💱 Отменить ордера конкретной пары")
    print("2. 🌐 Отменить ВСЕ ордера аккаунта")
    
    try:
        choice = input("\\nВаш выбор (1-2): ").strip()
        
        if choice == "1":
            symbol = input("💱 Введите торговую пару (например, BTCUSDT): ").strip().upper()
            if not symbol:
                print("❌ Торговая пара не указана")
                return None
            
            print(f"\\n⚠️ Будут отменены ВСЕ ордера для пары {symbol}")
            confirm = input("Подтвердите действие (yes/no): ").strip().lower()
            
            if confirm in ['yes', 'y', 'да']:
                return batch_cancel_orders(symbol)
            else:
                print("❌ Операция отменена")
                return None
                
        elif choice == "2":
            print("\\n⚠️ КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ!")
            print("🚨 Будут отменены ВСЕ открытые ордера во всех торговых парах!")
            print("🚨 Это действие НЕОБРАТИМО!")
            
            confirm1 = input("\\nВы уверены? Введите 'YES' для подтверждения: ").strip()
            if confirm1 != 'YES':
                print("❌ Операция отменена")
                return None
            
            confirm2 = input("Окончательное подтверждение. Введите 'CANCEL ALL': ").strip()
            if confirm2 != 'CANCEL ALL':
                print("❌ Операция отменена")
                return None
            
            return batch_cancel_orders()
        else:
            print("❌ Неверный выбор")
            return None
            
    except KeyboardInterrupt:
        print("\\n❌ Операция отменена пользователем")
        return None


def get_open_orders_count():
    """Получение количества открытых ордеров перед отменой"""
    config = load_config()
    if not config:
        return None
    
    # Получаем список открытых ордеров
    timestamp = str(int(time.time() * 1000))
    method = 'GET'
    request_path = '/api/v2/spot/trade/unfilled-orders'
    
    signature = generate_signature(timestamp, method, request_path)
    if not signature:
        return None
    
    headers = {
        'ACCESS-KEY': config['apiKey'],
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': config['passphrase'],
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }
    
    try:
        url = f"{config['baseURL']}{request_path}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '00000':
                orders = data.get('data', [])
                return len(orders)
        
        return 0
    except:
        return 0


def cancel_with_verification():
    """Отмена с предварительной проверкой количества ордеров"""
    print("🔍 ПРОВЕРКА ОТКРЫТЫХ ОРДЕРОВ")
    print("=" * 40)
    
    # Получаем количество открытых ордеров
    orders_count = get_open_orders_count()
    
    if orders_count is None:
        print("❌ Не удалось получить информацию об ордерах")
        return None
    elif orders_count == 0:
        print("ℹ️ Открытых ордеров не найдено")
        return None
    else:
        print(f"📊 Найдено открытых ордеров: {orders_count}")
        
        if orders_count > 10:
            print(f"⚠️ ВНИМАНИЕ: Большое количество ордеров ({orders_count})!")
        
        confirm = input(f"\\nПродолжить отмену {orders_count} ордеров? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y', 'да']:
            return batch_cancel_orders()
        else:
            print("❌ Операция отменена")
            return None


def main():
    """Основная функция"""
    print("🗑️ BITGET SPOT - ПАКЕТНАЯ ОТМЕНА ОРДЕРОВ")
    print("=" * 50)
    
    print("\\n🔌 Выберите режим:")
    print("1. 🗑️ Отменить все ордера")
    print("2. 💱 Отменить ордера пары")
    print("3. 🔍 Интерактивная отмена")
    print("4. ✅ Отмена с проверкой")
    
    try:
        choice = input("\\nВаш выбор (1-4): ").strip()
        
        if choice == "1":
            print("\\n⚠️ ВНИМАНИЕ: Будут отменены ВСЕ ордера!")
            confirm = input("Подтвердите (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                batch_cancel_orders()
            else:
                print("❌ Операция отменена")
                
        elif choice == "2":
            symbol = input("💱 Введите торговую пару: ").strip().upper()
            if symbol:
                batch_cancel_orders(symbol)
            else:
                print("❌ Торговая пара не указана")
                
        elif choice == "3":
            cancel_all_orders_interactive()
            
        elif choice == "4":
            cancel_with_verification()
            
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
