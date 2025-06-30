#!/usr/bin/env python3
"""
Получение статуса ордера на USDT Perpetual Futures на Bitget

Этот скрипт показывает детальную информацию об ордере:
- Статус исполнения
- Размер и цену
- Время создания
- Комиссии
"""

import json
import hmac
import hashlib
import base64
import time
import requests
from datetime import datetime


def load_config():
    """Загрузка конфигурации из файла"""
    try:
        with open('../../config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл config.json не найден!")
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


def make_authenticated_request(config, method, endpoint, params=None):
    """Выполнение аутентифицированного запроса"""
    timestamp = str(int(time.time() * 1000))
    query_string = ''
    body = ''
    
    if method.upper() == 'GET' and params:
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    elif method.upper() == 'POST' and params:
        body = json.dumps(params)
    
    signature = create_signature(timestamp, method, endpoint, query_string, body, config['secretKey'])
    
    headers = {
        'ACCESS-KEY': config['apiKey'],
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': config['passphrase'],
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }
    
    url = f"{config['baseURL']}{endpoint}"
    if query_string:
        url += f"?{query_string}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        else:
            response = requests.post(url, headers=headers, data=body, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Запрос выполнен успешно")
            print("📋 RAW JSON Response от биржи:")
            print("=" * 50)
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("=" * 50)
            
            return data
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return None


def get_order_status(config, symbol, order_id):
    """Получение статуса ордера по ID"""
    params = {
        'symbol': symbol,
        'productType': 'USDT-FUTURES',
        'orderId': order_id
    }
    
    response = make_authenticated_request(config, 'GET', '/api/v2/mix/order/detail', params)
    
    if response and response.get('code') == '00000':
        return response.get('data', {})
    return None


def get_open_orders(config, symbol=None):
    """Получение всех открытых ордеров"""
    params = {'productType': 'USDT-FUTURES'}
    if symbol:
        params['symbol'] = symbol
    
    response = make_authenticated_request(config, 'GET', '/api/v2/mix/order/orders-pending', params)
    
    if response and response.get('code') == '00000':
        return response.get('data', [])
    return []


def get_order_history(config, symbol=None, limit=10):
    """Получение истории ордеров"""
    params = {
        'productType': 'USDT-FUTURES',
        'pageSize': str(limit)
    }
    if symbol:
        params['symbol'] = symbol
    
    response = make_authenticated_request(config, 'GET', '/api/v2/mix/order/orders-history', params)
    
    if response and response.get('code') == '00000':
        return response.get('data', {}).get('orderList', [])
    return []


def display_order_info(order_info):
    """Отображение детальной информации об ордере"""
    if not order_info:
        print("❌ Информация об ордере не найдена")
        return
    
    print(f"\n📊 ДЕТАЛЬНАЯ ИНФОРМАЦИЯ ОБ ОРДЕРЕ")
    print("=" * 50)
    
    # Основная информация
    print(f"🆔 ID ордера: {order_info.get('orderId', 'N/A')}")
    print(f"👤 Client ID: {order_info.get('clientOid', 'N/A')}")
    print(f"💱 Символ: {order_info.get('symbol', 'N/A')}")
    print(f"🎯 Сторона: {order_info.get('side', 'N/A')}")
    print(f"📊 Тип ордера: {order_info.get('orderType', 'N/A')}")
    
    # Статус
    status = order_info.get('status', 'N/A')
    status_emoji = {
        'new': '🟡',
        'partial_filled': '🟠', 
        'filled': '✅',
        'cancelled': '❌',
        'expired': '⏰'
    }
    print(f"📋 Статус: {status_emoji.get(status, '⚪')} {status}")
    
    # Размеры и цены
    print(f"📏 Размер: {order_info.get('size', '0')}")
    print(f"✅ Исполнено: {order_info.get('filledQty', '0')}")
    print(f"📊 Средняя цена: {order_info.get('averagePrice', '0')}")
    print(f"💰 Цена ордера: {order_info.get('price', 'Market')}")
    
    # Время
    created_time = order_info.get('cTime')
    if created_time:
        dt = datetime.fromtimestamp(int(created_time) / 1000)
        print(f"⏰ Создан: {dt.strftime('%d.%m.%Y %H:%M:%S')}")
    
    updated_time = order_info.get('uTime')
    if updated_time:
        dt = datetime.fromtimestamp(int(updated_time) / 1000)
        print(f"🔄 Обновлен: {dt.strftime('%d.%m.%Y %H:%M:%S')}")
    
    # Финансовая информация
    print(f"💵 Маржинальная валюта: {order_info.get('marginCoin', 'N/A')}")
    print(f"💸 Комиссия: {order_info.get('fee', '0')}")
    print(f"⚖️ Режим маржи: {order_info.get('marginMode', 'N/A')}")
    
    # Дополнительная информация
    if order_info.get('reduceOnly'):
        print(f"🔒 Только закрытие: {order_info.get('reduceOnly')}")
    
    if order_info.get('timeInForceValue'):
        print(f"⏳ Время действия: {order_info.get('timeInForceValue')}")


def display_orders_table(orders, title="ОРДЕРА"):
    """Отображение таблицы ордеров"""
    if not orders or not isinstance(orders, list):
        print(f"📊 {title}: Нет ордеров")
        return
    
    print(f"\n📊 {title}")
    print("=" * 100)
    print(f"{'ID':<20} {'Символ':<10} {'Тип':<8} {'Сторона':<6} {'Размер':<10} {'Цена':<12} {'Статус':<12}")
    print("-" * 100)
    
    # Убеждаемся, что orders это список
    orders_list = list(orders) if not isinstance(orders, list) else orders
    
    for order in orders_list[:10]:  # Показываем первые 10
        if not isinstance(order, dict):
            continue
        
        order_id_full = order.get('orderId', 'N/A')
        order_id = order_id_full[:18] + '..' if len(str(order_id_full)) > 18 else str(order_id_full)
        symbol = order.get('symbol', 'N/A')
        order_type = order.get('orderType', 'N/A')
        side = order.get('side', 'N/A')
        size = order.get('size', '0')
        price = order.get('price', 'Market')
        status = order.get('status', 'N/A')
        
        print(f"{order_id:<20} {symbol:<10} {order_type:<8} {side:<6} {size:<10} {price:<12} {status:<12}")
    
    if len(orders_list) > 10:
        print(f"\n... и еще {len(orders_list) - 10} ордеров")


def main():
    """Основная функция"""
    print("📊 СТАТУС ОРДЕРОВ BITGET FUTURES")
    print("=" * 50)
    
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
    
    print("🔍 Выберите действие:")
    print("1. 📊 Показать все открытые ордера")
    print("2. 📋 Показать историю ордеров")
    print("3. 🔍 Проверить конкретный ордер по ID")
    
    choice = input("Ваш выбор (1-3): ").strip()
    
    if choice == "1":
        # Открытые ордера
        symbol = input("💱 Введите символ (Enter для всех): ").strip().upper()
        if not symbol:
            symbol = None
        
        print("🔄 Получение открытых ордеров...")
        open_orders = get_open_orders(config, symbol)
        display_orders_table(open_orders, "ОТКРЫТЫЕ ОРДЕРА")
        
    elif choice == "2":
        # История ордеров
        symbol = input("💱 Введите символ (Enter для всех): ").strip().upper()
        if not symbol:
            symbol = None
        
        limit = input("📊 Количество записей (по умолчанию 10): ").strip()
        try:
            limit = int(limit) if limit else 10
        except ValueError:
            limit = 10
        
        print("🔄 Получение истории ордеров...")
        history = get_order_history(config, symbol, limit)
        display_orders_table(history, "ИСТОРИЯ ОРДЕРОВ")
        
    elif choice == "3":
        # Конкретный ордер
        symbol = input("💱 Введите символ: ").strip().upper()
        order_id = input("🆔 Введите ID ордера: ").strip()
        
        if not symbol or not order_id:
            print("❌ Необходимо указать символ и ID ордера")
            return
        
        print("🔄 Получение информации об ордере...")
        order_info = get_order_status(config, symbol, order_id)
        display_order_info(order_info)
        
    else:
        print("❌ Неверный выбор")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
