#!/usr/bin/env python3
"""
Bitget API - Отмена всех ордеров (Spot)
Массовая отмена всех открытых ордеров пользователя

Официальная документация:
https://www.bitget.com/api-doc/spot/trade/Cancel-Batch-Orders

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
        with open('config.json', 'r') as f:
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

def get_open_orders(config, symbol=None):
    """Получение всех открытых ордеров"""
    params = {'limit': '100'}
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

def cancel_batch_orders(config, symbol, order_ids):
    """
    Отмена пакета ордеров
    
    Параметры:
    - symbol: Торговая пара (обязательно)
    - order_ids: Список ID ордеров для отмены (максимум 10 за раз)
    """
    
    # Ограничиваем до 10 ордеров за раз (лимит API)
    order_ids_batch = order_ids[:10]
    
    # Подготовка данных запроса
    request_data = {
        'symbol': symbol.upper(),
        'orderIds': order_ids_batch
    }
    
    body = json.dumps(request_data)
    
    # Параметры для подписи
    timestamp = str(int(time.time() * 1000))
    method = 'POST'
    request_path = '/api/v2/spot/trade/cancel-batch-orders'
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
        print(f"🔄 Отмена пакета из {len(order_ids_batch)} ордеров...")
        
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

def cancel_single_order(config, symbol, order_id):
    """Отмена одного ордера (fallback)"""
    request_data = {
        'symbol': symbol.upper(),
        'orderId': str(order_id)
    }
    
    body = json.dumps(request_data)
    timestamp = str(int(time.time() * 1000))
    method = 'POST'
    request_path = '/api/v2/spot/trade/cancel-order'
    query_string = ''
    
    signature = create_signature(timestamp, method, request_path, query_string, body, config['secretKey'])
    
    headers = {
        'ACCESS-KEY': config['apiKey'],
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': config['passphrase'],
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }
    
    url = f"{config['baseURL']}{request_path}"
    
    try:
        response = requests.post(url, headers=headers, data=body, timeout=config.get('timeout', 30))
        
        if response.status_code == 200:
            data = response.json()
            return data.get('code') == '00000'
        return False
    except:
        return False

def format_side(side):
    """Форматирование стороны ордера"""
    if side.lower() == 'buy':
        return '🟢'
    elif side.lower() == 'sell':
        return '🔴'
    else:
        return '❓'

def analyze_orders_for_cancellation(orders):
    """Анализ ордеров перед отменой"""
    if not orders:
        return
    
    print(f"\n📊 АНАЛИЗ ОРДЕРОВ ДЛЯ ОТМЕНЫ")
    print("=" * 50)
    
    # Группировка по парам
    symbols_orders = {}
    total_value = 0
    partially_filled_count = 0
    
    for order in orders:
        symbol = order.get('symbol', 'UNKNOWN')
        if symbol not in symbols_orders:
            symbols_orders[symbol] = {'orders': [], 'total_value': 0}
        
        symbols_orders[symbol]['orders'].append(order)
        
        # Расчет стоимости
        price = float(order.get('price', 0))
        size = float(order.get('size', 0))
        order_value = price * size if price > 0 and size > 0 else 0
        symbols_orders[symbol]['total_value'] += order_value
        total_value += order_value
        
        # Проверка на частичное исполнение
        filled_size = float(order.get('baseVolume', 0))
        if filled_size > 0:
            partially_filled_count += 1
    
    print(f"📈 Всего ордеров к отмене: {len(orders)}")
    print(f"💰 Общая стоимость: ${total_value:,.2f}")
    print(f"💱 Торговых пар: {len(symbols_orders)}")
    
    if partially_filled_count > 0:
        print(f"⚠️ Частично исполненных: {partially_filled_count}")
    
    # Детали по парам
    print(f"\n💎 Распределение по парам:")
    for symbol, data in symbols_orders.items():
        orders_count = len(data['orders'])
        total_val = data['total_value']
        print(f"   {symbol}: {orders_count} ордеров (${total_val:,.2f})")

def display_orders_summary(orders):
    """Краткая сводка ордеров"""
    if not orders:
        print("📭 Нет открытых ордеров для отмены")
        return False
    
    print(f"\n📋 ОРДЕРА К ОТМЕНЕ")
    print("=" * 70)
    print(f"🔢 Найдено ордеров: {len(orders)}")
    
    # Показываем первые 10 ордеров
    display_orders = orders[:10]
    
    print(f"\n{'№':<3} {'Пара':<10} {'🎯':<2} {'Цена':<12} {'Размер':<15} {'Стоимость':<12}")
    print("-" * 70)
    
    for i, order in enumerate(display_orders, 1):
        symbol = order.get('symbol', 'N/A')[:9]
        side = format_side(order.get('side', ''))
        
        price = float(order.get('price', 0))
        size = float(order.get('size', 0))
        order_value = price * size if price > 0 and size > 0 else 0
        
        price_str = f"${price:.4f}" if price > 0 else "Market"
        size_str = f"{size:.6f}".rstrip('0').rstrip('.')
        value_str = f"${order_value:.2f}" if order_value > 0 else "N/A"
        
        print(f"{i:<3} {symbol:<10} {side:<2} {price_str:<12} {size_str:<15} {value_str:<12}")
    
    if len(orders) > 10:
        print(f"... и еще {len(orders) - 10} ордеров")
    
    return True

def cancel_all_orders_by_symbol(config, symbol, orders):
    """Отмена всех ордеров для одной торговой пары"""
    order_ids = [order.get('orderId') for order in orders if order.get('orderId')]
    
    if not order_ids:
        print(f"❌ Нет ID ордеров для {symbol}")
        return 0, 0
    
    cancelled_count = 0
    failed_count = 0
    
    # Обработка пакетами по 10 ордеров
    for i in range(0, len(order_ids), 10):
        batch = order_ids[i:i+10]
        
        print(f"🔄 Обработка пакета {i//10 + 1} для {symbol} ({len(batch)} ордеров)...")
        
        result = cancel_batch_orders(config, symbol, batch)
        
        if result is not None:
            # Анализ результата пакетной отмены
            success_orders = result.get('successList', [])
            failed_orders = result.get('failureList', [])
            
            cancelled_count += len(success_orders)
            failed_count += len(failed_orders)
            
            print(f"✅ Успешно отменено: {len(success_orders)}")
            if failed_orders:
                print(f"❌ Не удалось отменить: {len(failed_orders)}")
        else:
            # Fallback - отмена по одному
            print(f"🔄 Пакетная отмена не удалась, пробуем по одному...")
            
            for order_id in batch:
                if cancel_single_order(config, symbol, order_id):
                    cancelled_count += 1
                    print(f"✅ Отменен ордер: {order_id}")
                else:
                    failed_count += 1
                    print(f"❌ Не удалось отменить: {order_id}")
                
                time.sleep(0.1)  # Небольшая задержка между запросами
    
    return cancelled_count, failed_count

def main():
    """Основная функция"""
    print("🗑️ ОТМЕНА ВСЕХ ОРДЕРОВ BITGET SPOT")
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
    
    print("\n🔧 Способы отмены:")
    print("1. Отменить ВСЕ открытые ордера")
    print("2. Отменить ордера конкретной торговой пары")
    
    choice = input("Ваш выбор (1-2): ").strip()
    
    symbol_filter = None
    if choice == "2":
        symbol_filter = input("💱 Введите символ пары (например, BTCUSDT): ").strip().upper()
        if not symbol_filter:
            print("❌ Символ пары обязателен!")
            return
    elif choice != "1":
        print("❌ Неверный выбор")
        return
    
    # Получение открытых ордеров
    print(f"\n🔄 Получение открытых ордеров...")
    orders = get_open_orders(config, symbol_filter)
    
    if not display_orders_summary(orders):
        return
    
    analyze_orders_for_cancellation(orders)
    
    # Предупреждения и подтверждения
    print(f"\n⚠️ ВАЖНЫЕ ПРЕДУПРЕЖДЕНИЯ!")
    print("=" * 40)
    print("🚨 Это действие НЕОБРАТИМО!")
    print("📊 Все выбранные ордера будут отменены")
    print("💰 Частично исполненные ордера тоже будут отменены")
    print("⏰ Вы можете потерять выгодные позиции")
    
    # Проверка на частично исполненные ордера
    partially_filled = [o for o in orders if float(o.get('baseVolume', 0)) > 0]
    if partially_filled:
        print(f"\n⚠️ ОБНАРУЖЕНЫ ЧАСТИЧНО ИСПОЛНЕННЫЕ ОРДЕРА!")
        print(f"🔢 Количество: {len(partially_filled)}")
        print(f"💡 При отмене вы получите только исполненную часть")
    
    # Первое подтверждение
    print(f"\n❓ ПЕРВОЕ ПОДТВЕРЖДЕНИЕ")
    if symbol_filter:
        confirm1 = input(f"Отменить все ордера для {symbol_filter}? (y/N): ").strip().lower()
    else:
        confirm1 = input(f"Отменить ВСЕ {len(orders)} открытых ордеров? (y/N): ").strip().lower()
    
    if confirm1 != 'y':
        print("❌ Отмена операции пользователем")
        return
    
    # Второе подтверждение (для безопасности)
    print(f"\n❓ ФИНАЛЬНОЕ ПОДТВЕРЖДЕНИЕ")
    confirm2 = input("⚠️ Вы УВЕРЕНЫ? Напишите 'ОТМЕНИТЬ ВСЕ' для подтверждения: ").strip()
    
    if confirm2 != 'ОТМЕНИТЬ ВСЕ':
        print("❌ Неверное подтверждение. Операция отменена.")
        return
    
    # Выполнение массовой отмены
    print(f"\n🔄 НАЧИНАЕМ МАССОВУЮ ОТМЕНУ ОРДЕРОВ...")
    print("=" * 50)
    
    start_time = time.time()
    total_cancelled = 0
    total_failed = 0
    
    # Группировка ордеров по торговым парам
    orders_by_symbol = {}
    for order in orders:
        symbol = order.get('symbol', 'UNKNOWN')
        if symbol not in orders_by_symbol:
            orders_by_symbol[symbol] = []
        orders_by_symbol[symbol].append(order)
    
    # Отмена по парам
    for symbol, symbol_orders in orders_by_symbol.items():
        print(f"\n💱 Обработка пары: {symbol} ({len(symbol_orders)} ордеров)")
        
        cancelled, failed = cancel_all_orders_by_symbol(config, symbol, symbol_orders)
        
        total_cancelled += cancelled
        total_failed += failed
        
        print(f"   ✅ Отменено: {cancelled}")
        if failed > 0:
            print(f"   ❌ Не удалось: {failed}")
    
    # Итоговый отчет
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 40)
    print(f"⏰ Время выполнения: {duration:.1f} сек")
    print(f"✅ Успешно отменено: {total_cancelled} ордеров")
    print(f"❌ Не удалось отменить: {total_failed} ордеров")
    print(f"📊 Общий успех: {(total_cancelled/(total_cancelled+total_failed)*100):.1f}%" if (total_cancelled+total_failed) > 0 else "N/A")
    
    if total_cancelled > 0:
        print(f"\n🎉 МАССОВАЯ ОТМЕНА ЗАВЕРШЕНА!")
        print(f"💡 Рекомендации:")
        print(f"   📊 Проверьте баланс: python get_account_balance.py")
        print(f"   📋 Убедитесь что все отменено: python get_open_orders.py")
    
    if total_failed > 0:
        print(f"\n⚠️ НЕКОТОРЫЕ ОРДЕРА НЕ ОТМЕНЕНЫ")
        print(f"🔍 Возможные причины:")
        print(f"   • Ордера исполнились во время отмены")
        print(f"   • Технические проблемы с API")
        print(f"   • Превышен rate limit")
        print(f"\n🛠️ Попробуйте:")
        print(f"   📋 Проверить оставшиеся ордера: python get_open_orders.py")
        print(f"   🔄 Повторить отмену через несколько минут")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена пользователем")
        print("⚠️ Некоторые ордера могли быть отменены!")
        print("🔍 Проверьте статус: python get_open_orders.py")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("🔧 Проверьте config.json и соединение с интернетом")
