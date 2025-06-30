#!/usr/bin/env python3
"""
Bitget API - История ордеров (Spot)
Получение истории исполненных ордеров пользователя

Официальная документация:
https://www.bitget.com/api-doc/spot/trade/Get-Order-History

Требует аутентификации: Да
Лимит запросов: 10 запросов/секунду
"""

import requests
import json
import hmac
import hashlib
import base64
import time
from datetime import datetime, timedelta

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

def get_orders_history(config, symbol=None, start_time=None, end_time=None, limit=100):
    """
    Получение истории ордеров
    
    Параметры:
    - symbol: Торговая пара (например, 'BTCUSDT'). Если None - все пары
    - start_time: Начальное время (timestamp в ms)
    - end_time: Конечное время (timestamp в ms)  
    - limit: Количество записей (1-100)
    """
    
    # Подготовка параметров запроса
    params = {
        'limit': str(min(limit, 100))  # Максимум 100 записей за запрос
    }
    
    if symbol:
        params['symbol'] = symbol.upper()
    
    if start_time:
        params['startTime'] = str(start_time)
        
    if end_time:
        params['endTime'] = str(end_time)
    
    # Формирование строки запроса
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    
    # Параметры для подписи
    timestamp = str(int(time.time() * 1000))
    method = 'GET'
    request_path = '/api/v2/spot/trade/fills'
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
        print(f"🔄 Запрос истории ордеров...")
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

def format_order_status(status):
    """Форматирование статуса ордера"""
    status_map = {
        'live': '🟡 Активный',
        'partially_filled': '🟠 Частично',
        'filled': '🟢 Исполнен',
        'cancelled': '🔴 Отменен',
        'new': '🔵 Новый'
    }
    return status_map.get(status, f"❓ {status}")

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

def analyze_orders(orders):
    """Анализ ордеров"""
    if not orders:
        return
    
    print(f"\n📊 АНАЛИЗ ОРДЕРОВ")
    print("=" * 50)
    
    # Статистика по статусам
    status_count = {}
    total_volume = 0
    total_fees = 0
    symbols_traded = set()
    
    for order in orders:
        status = order.get('status', 'unknown')
        status_count[status] = status_count.get(status, 0) + 1
        
        if order.get('fillNotionalUsd'):
            total_volume += float(order['fillNotionalUsd'])
        
        if order.get('feeDetail'):
            # Суммируем комиссии (может быть массив)
            fee_detail = order['feeDetail']
            if isinstance(fee_detail, list):
                for fee in fee_detail:
                    if fee.get('totalFee'):
                        total_fees += abs(float(fee['totalFee']))
        
        symbols_traded.add(order.get('symbol', ''))
    
    print(f"📈 Общий объем торгов: ${total_volume:,.2f}")
    print(f"💸 Общие комиссии: ${total_fees:.4f}")
    print(f"💱 Торговых пар: {len(symbols_traded)}")
    
    print(f"\n📊 Статистика по статусам:")
    for status, count in status_count.items():
        formatted_status = format_order_status(status)
        percentage = (count / len(orders)) * 100
        print(f"   {formatted_status}: {count} ({percentage:.1f}%)")
    
    # Топ торговых пар
    if len(symbols_traded) > 1:
        symbol_volume = {}
        for order in orders:
            symbol = order.get('symbol', '')
            volume = float(order.get('fillNotionalUsd', 0))
            symbol_volume[symbol] = symbol_volume.get(symbol, 0) + volume
        
        print(f"\n💎 Топ торговых пар по объему:")
        sorted_symbols = sorted(symbol_volume.items(), key=lambda x: x[1], reverse=True)
        for i, (symbol, volume) in enumerate(sorted_symbols[:5], 1):
            print(f"   {i}. {symbol}: ${volume:,.2f}")

def display_orders(orders):
    """Отображение списка ордеров в табличном формате"""
    if not orders:
        print("📭 Нет ордеров для отображения")
        return
    
    print(f"\n📋 ИСТОРИЯ ОРДЕРОВ")
    print("=" * 80)
    print(f"🔢 Найдено ордеров: {len(orders)}")
    
    # Подготовка данных для таблицы
    table_data = []
    
    for order in orders:
        # Преобразование времени
        create_time = int(order.get('cTime', 0))
        if create_time:
            dt = datetime.fromtimestamp(create_time / 1000)
            time_str = dt.strftime('%d.%m %H:%M')
        else:
            time_str = "N/A"
        
        # Форматирование данных
        symbol = order.get('symbol', 'N/A')
        side = format_side(order.get('side', ''))
        order_type = format_order_type(order.get('orderType', ''))
        status = format_order_status(order.get('status', ''))
        
        # Цены и количества
        price = float(order.get('price', 0))
        size = float(order.get('size', 0))
        filled_size = float(order.get('baseVolume', 0))
        
        # Объем в USDT
        filled_notional = float(order.get('fillNotionalUsd', 0))
        
        # Процент исполнения
        if size > 0:
            fill_pct = (filled_size / size) * 100
            fill_str = f"{fill_pct:.1f}%"
        else:
            fill_str = "0%"
        
        table_data.append([
            time_str,
            symbol,
            side.split()[1] if ' ' in side else side,  # Убираем эмодзи для таблицы
            order_type.split()[1] if ' ' in order_type else order_type,
            f"${price:.4f}" if price > 0 else "Market",
            f"{size:.6f}",
            fill_str,
            f"${filled_notional:.2f}",
            status.split()[1] if ' ' in status else status
        ])
    
    # Заголовки таблицы
    headers = [
        "Время", "Пара", "Сторона", "Тип", 
        "Цена", "Размер", "Исполн.", "Объем USD", "Статус"
    ]
    
    # Отображение таблицы
    print(tabulate(table_data, headers=headers, tablefmt="grid", stralign="center"))

def main():
    """Основная функция"""
    print("📋 ИСТОРИЯ ОРДЕРОВ BITGET SPOT")
    print("=" * 50)
    
    # Загрузка конфигурации
    config = load_config()
    if not config:
        return
    
    # Получение истории ордеров без интерактивного ввода
    # Используем последние 7 дней, все пары, лимит 50
    from datetime import timedelta
    start_time = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
    orders = get_orders_history(config, symbol=None, start_time=start_time, end_time=None, limit=50)
    
    if orders is not None:
        import json
        print("\n� RAW JSON RESPONSE:")
        print(json.dumps(orders, indent=2, ensure_ascii=False))
        
        print(f"\n📊 Найдено ордеров за последние 7 дней: {len(orders)}")
        if orders:
            print("� Показана полная история ордеров")
        else:
            print("✅ Нет ордеров за указанный период")
    else:
        print("❌ Не удалось получить историю ордеров")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("🔧 Проверьте config.json и соединение с интернетом")
