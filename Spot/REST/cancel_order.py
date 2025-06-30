#!/usr/bin/env python3
"""
Bitget API - Отмена ордера (Spot)
Отмена конкретного открытого ордера по ID

Официальная документация:
https://www.bitget.com/api-doc/spot/trade/Cancel-Order

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

def get_open_orders_for_selection(config, symbol=None):
    """Получение списка открытых ордеров для выбора"""
    params = {'limit': '50'}
    if symbol:
        params['symbol'] = symbol.upper()
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    timestamp = str(int(time.time() * 1000))
    method = 'GET'
    request_path = '/api/v2/spot/trade/orders-pending'
    body = ''
    
    signature = create_signature(timestamp, method, request_path, query_string, body, config['secretKey'])
    
    headers = {
        'ACCESS-KEY': config['apiKey'],
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': config['passphrase'],
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }
    
    url = f"{config['baseURL']}{request_path}?{query_string}"
    
    try:
        response = requests.get(url, headers=headers, timeout=config.get('timeout', 30))
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '00000':
                return data.get('data', [])
        return []
    except:
        return []

def cancel_order(config, symbol, order_id):
    """
    Отмена ордера
    
    Параметры:
    - symbol: Торговая пара (обязательно)
    - order_id: ID ордера для отмены (обязательно)
    """
    
    # Подготовка данных запроса
    request_data = {
        'symbol': symbol.upper(),
        'orderId': str(order_id)
    }
    
    body = json.dumps(request_data)
    
    # Параметры для подписи
    timestamp = str(int(time.time() * 1000))
    method = 'POST'
    request_path = '/api/v2/spot/trade/cancel-order'
    query_string = ''
    
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
    url = f"{config['baseURL']}{request_path}"
    
    try:
        print(f"🔄 Отправка запроса на отмену ордера...")
        print(f"💱 Пара: {symbol}")
        print(f"🆔 ID ордера: {order_id}")
        
        response = requests.post(url, headers=headers, data=body, timeout=config.get('timeout', 30))
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == '00000':
                return data.get('data', {})
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

def format_side(side):
    """Форматирование стороны ордера"""
    if side.lower() == 'buy':
        return '🟢 Покупка'
    elif side.lower() == 'sell':
        return '🔴 Продажа'
    else:
        return f"❓ {side}"

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

def display_orders_for_selection(orders):
    """Отображение ордеров для выбора отмены"""
    if not orders:
        print("📭 Нет открытых ордеров для отмены")
        return False
    
    print(f"\n📋 ОТКРЫТЫЕ ОРДЕРА ДЛЯ ОТМЕНЫ")
    print("=" * 80)
    print(f"🔢 Найдено ордеров: {len(orders)}")
    
    print(f"\n{'№':<3} {'ID ордера':<15} {'Пара':<10} {'Сторона':<10} {'Цена':<12} {'Размер':<15} {'Стоимость':<12}")
    print("-" * 80)
    
    for i, order in enumerate(orders, 1):
        order_id = order.get('orderId', 'N/A')[:14]
        symbol = order.get('symbol', 'N/A')[:9]
        side = '🟢 BUY' if order.get('side', '').lower() == 'buy' else '🔴 SELL'
        
        price = float(order.get('price', 0))
        size = float(order.get('size', 0))
        order_value = price * size if price > 0 and size > 0 else 0
        
        price_str = f"${price:.4f}" if price > 0 else "Market"
        size_str = f"{size:.6f}".rstrip('0').rstrip('.')
        value_str = f"${order_value:.2f}" if order_value > 0 else "N/A"
        
        print(f"{i:<3} {order_id:<15} {symbol:<10} {side:<10} {price_str:<12} {size_str:<15} {value_str:<12}")
    
    return True

def display_order_details(order):
    """Подробная информация об ордере перед отменой"""
    print(f"\n📋 ДЕТАЛИ ОРДЕРА")
    print("=" * 40)
    
    # Время создания
    create_time = int(order.get('cTime', 0))
    if create_time:
        dt = datetime.fromtimestamp(create_time / 1000)
        time_str = dt.strftime('%d.%m.%Y %H:%M:%S')
    else:
        time_str = "N/A"
    
    # Основная информация
    order_id = order.get('orderId', 'N/A')
    symbol = order.get('symbol', 'N/A')
    side = format_side(order.get('side', ''))
    order_type = format_order_type(order.get('orderType', ''))
    
    price = float(order.get('price', 0))
    size = float(order.get('size', 0))
    filled_size = float(order.get('baseVolume', 0))
    order_value = price * size if price > 0 and size > 0 else 0
    
    # Процент исполнения
    fill_percentage = (filled_size / size * 100) if size > 0 else 0
    
    print(f"🆔 ID ордера: {order_id}")
    print(f"⏰ Время создания: {time_str}")
    print(f"💱 Торговая пара: {symbol}")
    print(f"📊 Тип: {order_type}")
    print(f"🎯 Сторона: {side}")
    print(f"💰 Цена: ${price:.4f}" if price > 0 else "💰 Цена: Рыночная")
    print(f"📏 Размер: {size:.6f}")
    print(f"💵 Стоимость: ${order_value:.2f}" if order_value > 0 else "💵 Стоимость: N/A")
    print(f"✅ Исполнено: {filled_size:.6f} ({fill_percentage:.1f}%)")

def calculate_potential_loss(order):
    """Расчет потенциальной потери от отмены ордера"""
    filled_size = float(order.get('baseVolume', 0))
    
    if filled_size > 0:
        print(f"\n⚠️ ВНИМАНИЕ!")
        print("=" * 30)
        print(f"🔄 Ордер частично исполнен: {filled_size:.6f}")
        print(f"❗ При отмене вы получите только исполненную часть")
        print(f"💡 Рассмотрите возможность оставить ордер активным")
        return True
    
    return False

def main():
    """Основная функция"""
    print("🗑️ ОТМЕНА ОРДЕРА BITGET SPOT")
    print("=" * 50)
    
    # Загрузка конфигурации
    config = load_config()
    if not config:
        return
    
    # Проверка наличия необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase', 'baseURL']
    for key in required_keys:
        if not config.get(key):
            print(f"❌ Отсутствует ключ '{key}' в config.json")
            return
    
    print("\n🔧 Способы отмены ордера:")
    print("1. Выбрать из списка открытых ордеров")
    print("2. Ввести ID ордера и символ вручную")
    
    choice = input("Ваш выбор (1-2): ").strip()
    
    if choice == "1":
        # Выбор из списка открытых ордеров
        print("\n🔄 Получение списка открытых ордеров...")
        
        # Опциональная фильтрация по паре
        symbol_filter = input("💱 Фильтр по паре (Enter для всех пар): ").strip().upper()
        if not symbol_filter:
            symbol_filter = None
        
        # Получение открытых ордеров
        orders = get_open_orders_for_selection(config, symbol_filter)
        
        if not display_orders_for_selection(orders):
            return
        
        # Выбор ордера
        try:
            order_index = int(input(f"\n🔢 Выберите номер ордера (1-{len(orders)}): ")) - 1
            if 0 <= order_index < len(orders):
                selected_order = orders[order_index]
                symbol = selected_order.get('symbol')
                order_id = selected_order.get('orderId')
            else:
                print("❌ Неверный номер ордера")
                return
        except ValueError:
            print("❌ Неверный формат номера")
            return
    
    elif choice == "2":
        # Ручной ввод
        symbol = input("💱 Введите символ пары (например, BTCUSDT): ").strip().upper()
        if not symbol:
            print("❌ Символ пары обязателен!")
            return
        
        order_id = input("🆔 Введите ID ордера: ").strip()
        if not order_id:
            print("❌ ID ордера обязателен!")
            return
        
        selected_order = None  # Для ручного ввода детали не показываем
    
    else:
        print("❌ Неверный выбор")
        return
    
    # Отображение деталей ордера (если доступны)
    if selected_order:
        display_order_details(selected_order)
        has_partial_fill = calculate_potential_loss(selected_order)
    else:
        print(f"\n🎯 ОТМЕНА ОРДЕРА")
        print("=" * 30)
        print(f"💱 Пара: {symbol}")
        print(f"🆔 ID: {order_id}")
        has_partial_fill = False
    
    # Подтверждение отмены
    print(f"\n❓ ПОДТВЕРЖДЕНИЕ ОТМЕНЫ")
    if has_partial_fill:
        confirm = input("⚠️ Ордер частично исполнен! Все равно отменить? (y/N): ").strip().lower()
    else:
        confirm = input("✅ Подтвердите отмену ордера (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Отмена ордера отклонена пользователем")
        return
    
    # Выполнение отмены
    print(f"\n🔄 Отмена ордера...")
    result = cancel_order(config, symbol, order_id)
    
    if result is not None:
        print(f"\n✅ ОРДЕР УСПЕШНО ОТМЕНЕН!")
        print("=" * 40)
        print(f"🆔 ID отмененного ордера: {order_id}")
        print(f"💱 Торговая пара: {symbol}")
        print(f"⏰ Время отмены: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        
        # Дополнительная информация если есть
        if 'orderId' in result:
            print(f"✅ Подтверждение от биржи: {result['orderId']}")
        
        print(f"\n💡 Рекомендации:")
        print(f"   📊 Проверьте баланс: python get_account_balance.py")
        print(f"   📋 Проверьте открытые ордера: python get_open_orders.py")
        
    else:
        print(f"\n❌ НЕ УДАЛОСЬ ОТМЕНИТЬ ОРДЕР")
        print("=" * 40)
        print(f"🔍 Возможные причины:")
        print(f"   • Ордер уже исполнен")
        print(f"   • Ордер уже отменен")
        print(f"   • Неверный ID ордера")
        print(f"   • Неверный символ пары")
        print(f"   • Технические проблемы с API")
        
        print(f"\n🛠️ Что попробовать:")
        print(f"   📋 Проверить список открытых ордеров: python get_open_orders.py")
        print(f"   📚 Проверить историю ордеров: python get_orders.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("🔧 Проверьте config.json и соединение с интернетом")
