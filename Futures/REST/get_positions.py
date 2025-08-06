#!/usr/bin/env python3
"""
Bitget API - Получение открытых позиций (USDT Perpetual Futures)
Получение информации о всех открытых позициях на фьючерсах

Официальная документация:
https://www.bitget.com/api-doc/contract/position/Get-Position-Information

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

def get_positions(config, product_type='USDT-FUTURES'):
    """Получение открытых позиций"""
    
    params = {
        'productType': product_type
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    timestamp = str(int(time.time() * 1000))
    method = 'GET'
    request_path = '/api/v2/mix/position/all-position'
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
        print("🚀 Bitget USDT Perpetual Futures - Open Positions")
        print("=" * 55)
        print("🔄 Получение открытых позиций...")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        # Сохранение примера ответа
        response_data = response.json() if response.status_code == 200 else {"error": response.text}
        save_response_example('futures_positions', {
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

def display_positions(positions):
    """Отображение информации о позициях"""
    
    if not positions:
        print("📭 Нет открытых позиций")
        return
    
    # Фильтруем только позиции с размером > 0
    active_positions = [pos for pos in positions if float(pos.get('total', 0)) != 0]
    
    if not active_positions:
        print("📭 Нет активных позиций")
        return
    
    print(f"📊 ОТКРЫТЫЕ ПОЗИЦИИ ({len(active_positions)} шт.)")
    print("=" * 80)
    
    total_unrealized_pnl = 0
    total_notional = 0
    
    for i, position in enumerate(active_positions, 1):
        symbol = position.get('symbol', 'N/A')
        side = position.get('holdSide', 'N/A')
        size = float(position.get('total', 0))
        available = float(position.get('available', 0))
        locked = float(position.get('locked', 0))
        margin = float(position.get('margin', 0))
        unrealized_pnl = float(position.get('unrealizedPL', 0))
        unrealized_pnl_rate = float(position.get('unrealizedPLR', 0))
        leverage = position.get('leverage', 'N/A')
        margin_mode = position.get('marginMode', 'N/A')
        avg_price = float(position.get('averageOpenPrice', 0))
        mark_price = float(position.get('markPrice', 0))
        
        # Расчет стоимости позиции
        notional_value = size * mark_price
        total_notional += notional_value
        total_unrealized_pnl += unrealized_pnl
        
        print(f"\n📈 ПОЗИЦИЯ #{i}: {symbol}")
        print("-" * 40)
        
        # Основная информация
        side_emoji = "🟢" if side == "long" else "🔴" if side == "short" else "⚪"
        print(f"🎯 Сторона: {side_emoji} {side.upper()}")
        print(f"📏 Размер: {size} контрактов")
        print(f"💰 Доступно: {available} | 🔒 Заблокировано: {locked}")
        
        # Ценовая информация
        print(f"💵 Средняя цена открытия: ${avg_price:.4f}")
        print(f"📊 Текущая марк-цена: ${mark_price:.4f}")
        print(f"💸 Стоимость позиции: ${notional_value:.2f}")
        
        # P&L информация
        pnl_emoji = "🟢" if unrealized_pnl >= 0 else "🔴"
        print(f"📈 Нереализованная P&L: {pnl_emoji} ${unrealized_pnl:.4f} ({unrealized_pnl_rate:.2%})")
        
        # Маржа и плечо
        print(f"⚖️ Режим маржи: {margin_mode}")
        print(f"🔢 Плечо: {leverage}x")
        print(f"💳 Использованная маржа: ${margin:.4f}")
        
        # Дополнительные поля
        liquidation_price = position.get('liquidationPrice')
        if liquidation_price and float(liquidation_price) > 0:
            print(f"⚠️ Цена ликвидации: ${float(liquidation_price):.4f}")
        
        auto_close_at = position.get('autoMarginReductionPriority')
        if auto_close_at:
            print(f"🔄 Приоритет авто-закрытия: {auto_close_at}")
    
    # Итоговая статистика
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    print("=" * 30)
    print(f"🔢 Всего позиций: {len(active_positions)}")
    print(f"💰 Общая стоимость позиций: ${total_notional:.2f}")
    
    total_pnl_emoji = "🟢" if total_unrealized_pnl >= 0 else "🔴"
    print(f"📈 Общая нереализованная P&L: {total_pnl_emoji} ${total_unrealized_pnl:.4f}")
    
    if total_notional > 0:
        total_pnl_rate = (total_unrealized_pnl / total_notional) * 100
        print(f"📊 Общий процент P&L: {total_pnl_emoji} {total_pnl_rate:.2f}%")
    
    print(f"\n💡 УПРАВЛЕНИЕ ПОЗИЦИЯМИ:")
    print("-" * 25)
    print("📝 Для размещения ордера: python place_limit_order.py")
    print("🔄 Для закрытия позиции: python place_market_order.py")
    print("⚙️ Для изменения плеча: python set_leverage.py")

def main():
    config_path = Path(__file__).parent.parent.parent / "config.json"
    with open(config_path, 'r') as file:
        config = json.load(file)
    
    # Получение позиций
    positions = get_positions(config)
    
    if positions is not None:
        print("✅ Информация о позициях получена успешно!")
    else:
        print("❌ Не удалось получить информацию о позициях")

if __name__ == "__main__":
    main()
