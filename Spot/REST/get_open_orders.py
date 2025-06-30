#!/usr/bin/env python3
"""
Bitget API - Открытые ордера (Spot)
Получение списка всех открытых (активных) ордеров пользователя

Официальная документация:
https://www.bitget.com/api-doc/spot/trade/Get-Open-Orders

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

def load_config():
    """Загрузка конфигурации из файла"""
    try:
        with open('../../config.json', 'r') as f:
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

def get_open_orders(config, symbol=None, limit=100):
    """
    Получение открытых ордеров
    
    Параметры:
    - symbol: Торговая пара (например, 'BTCUSDT'). Если None - все пары
    - limit: Количество записей (1-100)
    """
    
    # Подготовка параметров запроса
    params = {
        'limit': str(min(limit, 100))
    }
    
    if symbol:
        params['symbol'] = symbol.upper()
    
    # Формирование строки запроса
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    
    # Параметры для подписи
    timestamp = str(int(time.time() * 1000))
    method = 'GET'
    request_path = '/api/v2/spot/trade/unfilled-orders'
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
        print(f"🔄 Запрос открытых ордеров...")
        if symbol:
            print(f"💱 Пара: {symbol}")
        
        response = requests.get(url, headers=headers, timeout=config.get('timeout', 30))
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == '00000':
                return data.get('data', [])
            else:
                print(f"❌ Ошибка API: {data.get('msg')}")
                return None
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Превышено время ожидания запроса")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return None
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return None

def format_order_type(order_type):
    """Форматирование типа ордера"""
    type_map = {
        'limit': '📊 Лимитный',
        'market': '⚡ Рыночный',
        'post_only': '📌 Post Only',
        'fok': '🎯 FOK',
        'ioc': '⏱️ IOC'
    }
    return type_map.get(order_type, f"❓ {order_type}")

def format_side(side):
    """Форматирование стороны ордера"""
    if side.lower() == 'buy':
        return '🟢 Покупка'
    elif side.lower() == 'sell':
        return '🔴 Продажа'
    else:
        return f"❓ {side}"

def format_status(status):
    """Форматирование статуса ордера"""
    status_map = {
        'live': '🟡 Активный',
        'new': '🔵 Новый',
        'partially_filled': '🟠 Частично исполнен'
    }
    return status_map.get(status, f"❓ {status}")

def calculate_order_value(order):
    """Расчет стоимости ордера"""
    try:
        price = float(order.get('price', 0))
        size = float(order.get('size', 0))
        
        if price > 0 and size > 0:
            return price * size
        return 0
    except (ValueError, TypeError):
        return 0

def calculate_distance_from_market(order, market_price):
    """Расчет расстояния ордера от рыночной цены"""
    try:
        order_price = float(order.get('price', 0))
        if order_price <= 0 or market_price <= 0:
            return 0, 0
        
        distance = abs(order_price - market_price)
        distance_pct = (distance / market_price) * 100
        
        return distance, distance_pct
    except (ValueError, TypeError):
        return 0, 0

def analyze_open_orders(orders):
    """Анализ открытых ордеров"""
    if not orders:
        return
    
    print(f"\n📊 АНАЛИЗ ОТКРЫТЫХ ОРДЕРОВ")
    print("=" * 50)
    
    # Общая статистика
    total_buy_orders = 0
    total_sell_orders = 0
    total_buy_value = 0
    total_sell_value = 0
    
    symbols_count = {}
    order_types_count = {}
    
    for order in orders:
        side = order.get('side', '').lower()
        order_value = calculate_order_value(order)
        symbol = order.get('symbol', 'UNKNOWN')
        order_type = order.get('orderType', 'unknown')
        
        # Счетчики по сторонам
        if side == 'buy':
            total_buy_orders += 1
            total_buy_value += order_value
        elif side == 'sell':
            total_sell_orders += 1
            total_sell_value += order_value
        
        # Счетчики по символам
        symbols_count[symbol] = symbols_count.get(symbol, 0) + 1
        
        # Счетчики по типам ордеров
        order_types_count[order_type] = order_types_count.get(order_type, 0) + 1
    
    total_orders = len(orders)
    total_value = total_buy_value + total_sell_value
    
    print(f"📈 Всего ордеров: {total_orders}")
    print(f"🟢 Ордеров на покупку: {total_buy_orders} (${total_buy_value:,.2f})")
    print(f"🔴 Ордеров на продажу: {total_sell_orders} (${total_sell_value:,.2f})")
    print(f"💰 Общая стоимость: ${total_value:,.2f}")
    
    # Статистика по торговым парам
    if len(symbols_count) > 1:
        print(f"\n💱 Распределение по парам:")
        sorted_symbols = sorted(symbols_count.items(), key=lambda x: x[1], reverse=True)
        for symbol, count in sorted_symbols:
            percentage = (count / total_orders) * 100
            print(f"   {symbol}: {count} ордеров ({percentage:.1f}%)")
    
    # Статистика по типам ордеров
    print(f"\n📊 Типы ордеров:")
    for order_type, count in order_types_count.items():
        formatted_type = format_order_type(order_type)
        percentage = (count / total_orders) * 100
        print(f"   {formatted_type}: {count} ({percentage:.1f}%)")

def display_orders(orders):
    """Отображение списка открытых ордеров"""
    if not orders:
        print("📭 Нет открытых ордеров")
        return
    
    print(f"\n📋 ОТКРЫТЫЕ ОРДЕРА")
    print("=" * 100)
    print(f"🔢 Найдено ордеров: {len(orders)}")
    
    # Заголовок таблицы
    print(f"\n{'ID ордера':<15} {'Время':<12} {'Пара':<10} {'Сторона':<8} {'Тип':<10} {'Цена':<12} {'Размер':<15} {'Стоимость':<12} {'Статус':<10}")
    print("-" * 100)
    
    for order in orders:
        # Форматирование данных
        order_id = order.get('orderId', 'N/A')[:14]
        
        # Время создания
        create_time = int(order.get('cTime', 0))
        if create_time:
            dt = datetime.fromtimestamp(create_time / 1000)
            time_str = dt.strftime('%d.%m %H:%M')
        else:
            time_str = "N/A"
        
        symbol = order.get('symbol', 'N/A')[:9]
        side = '🟢 BUY' if order.get('side', '').lower() == 'buy' else '🔴 SELL'
        order_type = order.get('orderType', 'N/A')[:9]
        
        # Цена и размеры
        price = float(order.get('price', 0))
        size = float(order.get('size', 0))
        order_value = calculate_order_value(order)
        
        # Статус
        status = format_status(order.get('status', ''))
        status_short = status.split()[1] if ' ' in status else status[:9]
        
        # Форматирование для отображения
        price_str = f"${price:.4f}" if price > 0 else "Market"
        size_str = f"{size:.6f}".rstrip('0').rstrip('.')
        value_str = f"${order_value:.2f}" if order_value > 0 else "N/A"
        
        print(f"{order_id:<15} {time_str:<12} {symbol:<10} {side:<8} {order_type:<10} {price_str:<12} {size_str:<15} {value_str:<12} {status_short:<10}")

def display_order_summary(orders):
    """Краткая сводка по открытым ордерам"""
    if not orders:
        return
    
    print(f"\n🎯 КРАТКАЯ СВОДКА")
    print("=" * 40)
    
    # Последние 3 ордера
    recent_orders = orders[:3]
    
    for i, order in enumerate(recent_orders, 1):
        create_time = int(order.get('cTime', 0))
        if create_time:
            dt = datetime.fromtimestamp(create_time / 1000)
            time_str = dt.strftime('%d.%m.%Y %H:%M')
        else:
            time_str = "N/A"
        
        symbol = order.get('symbol', 'N/A')
        side = format_side(order.get('side', ''))
        price = float(order.get('price', 0))
        size = float(order.get('size', 0))
        order_value = calculate_order_value(order)
        
        print(f"#{i} [{time_str}]")
        print(f"   💱 {symbol} • {side}")
        print(f"   💰 ${price:.4f} • Размер: {size:.6f}")
        print(f"   💵 Стоимость: ${order_value:.2f}")
        print()

def check_order_risks(orders):
    """Проверка потенциальных рисков ордеров"""
    if not orders:
        return
    
    print(f"\n⚠️ АНАЛИЗ РИСКОВ")
    print("=" * 30)
    
    risks_found = []
    
    # Проверка на очень старые ордера
    current_time = time.time() * 1000
    old_orders = []
    
    for order in orders:
        create_time = int(order.get('cTime', 0))
        if create_time:
            age_hours = (current_time - create_time) / (1000 * 60 * 60)
            if age_hours > 24:  # Старше 24 часов
                old_orders.append((order, age_hours))
    
    if old_orders:
        risks_found.append(f"📅 Старые ордера: {len(old_orders)} ордеров старше 24ч")
    
    # Проверка на большое количество ордеров
    if len(orders) > 20:
        risks_found.append(f"📊 Много ордеров: {len(orders)} активных ордеров")
    
    # Проверка на концентрацию в одной паре
    symbols_count = {}
    for order in orders:
        symbol = order.get('symbol', '')
        symbols_count[symbol] = symbols_count.get(symbol, 0) + 1
    
    for symbol, count in symbols_count.items():
        if count > len(orders) * 0.7:  # Более 70% ордеров в одной паре
            risks_found.append(f"⚖️ Концентрация: {count} ордеров в {symbol}")
    
    # Проверка на очень большие ордера
    large_orders = []
    for order in orders:
        order_value = calculate_order_value(order)
        if order_value > 10000:  # Ордера больше $10,000
            large_orders.append((order, order_value))
    
    if large_orders:
        risks_found.append(f"💰 Крупные ордера: {len(large_orders)} ордеров > $10k")
    
    if risks_found:
        for risk in risks_found:
            print(f"   {risk}")
    else:
        print("   ✅ Критических рисков не обнаружено")

def main():
    """Основная функция"""
    print("📋 ОТКРЫТЫЕ ОРДЕРА BITGET SPOT")
    print("=" * 50)
    
    # Загрузка конфигурации
    config = load_config()
    if not config:
        return
    
    # Получение открытых ордеров без интерактивного ввода
    orders = get_open_orders(config, symbol=None, limit=100)
    
    if orders is not None:
        import json
        print("\n📄 RAW JSON RESPONSE:")
        print(json.dumps(orders, indent=2, ensure_ascii=False))
        
        print(f"\n� Найдено открытых ордеров: {len(orders)}")
        if orders:
            print("� Также показаны другие данные анализа")
            display_order_summary(orders)
        else:
            print("✅ Нет открытых ордеров")
    else:
        print("❌ Не удалось получить список открытых ордеров")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("🔧 Проверьте config.json и соединение с интернетом")
