#!/usr/bin/env python3
"""
Bitget USDT Perpetual REST API - Place Stop Limit Order

Размещение стоп-лимит ордера для фьючерсов.
Ордер становится лимитным при достижении стоп-цены.

Документация: https://www.bitget.com/api-doc/contract/trade/Place-Order

Параметры:
- symbol: торговая пара (обязательный)
- side: сторона (buy/sell)
- size: размер позиции
- triggerPrice: стоп-цена срабатывания
- price: лимитная цена исполнения
- orderType: stop_limit
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


def place_stop_limit_order(symbol, side, size, trigger_price, limit_price, client_oid=None):
    """
    Размещение стоп-лимит ордера
    
    Args:
        symbol (str): Торговая пара (например, BTCUSDT)
        side (str): Сторона (buy/sell)
        size (str): Размер позиции
        trigger_price (str): Стоп-цена срабатывания
        limit_price (str): Лимитная цена исполнения
        client_oid (str, optional): Клиентский ID ордера
    
    Returns:
        dict: Ответ API с данными ордера
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
    
    # Валидация параметров
    if side not in ['buy', 'sell']:
        print("❌ Сторона должна быть 'buy' или 'sell'")
        return None
    
    # Подготавливаем данные запроса
    timestamp = str(int(time.time() * 1000))
    method = 'POST'
    request_path = '/api/v2/mix/order/place-order'
    
    # Генерируем клиентский ID если не предоставлен
    if not client_oid:
        client_oid = f"stop_limit_{int(time.time())}"
    
    body_data = {
        'symbol': symbol,
        'productType': 'USDT-FUTURES',
        'marginMode': 'crossed',
        'marginCoin': 'USDT',
        'side': side,
        'orderType': 'stop_limit',
        'size': str(size),
        'price': str(limit_price),
        'triggerPrice': str(trigger_price),
        'clientOid': client_oid
    }
    
    body = json.dumps(body_data)
    
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
        
        side_emoji = "🟢" if side == "buy" else "🔴"
        print(f"🎯 Размещение стоп-лимит ордера...")
        print(f"💱 Пара: {symbol}")
        print(f"{side_emoji} Сторона: {side.upper()}")
        print(f"📊 Размер: {size}")
        print(f"🛑 Стоп-цена: ${trigger_price}")
        print(f"💰 Лимит-цена: ${limit_price}")
        print(f"🆔 Client OID: {client_oid}")
        
        response = requests.post(url, headers=headers, data=body)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == '00000':
                order_data = data.get('data', {})
                
                print("\\n✅ Стоп-лимит ордер успешно размещен!")
                print("=" * 50)
                
                # Информация об ордере
                order_id = order_data.get('orderId', 'N/A')
                client_order_id = order_data.get('clientOid', client_oid)
                
                print(f"🆔 ID ордера: {order_id}")
                print(f"👤 Client OID: {client_order_id}")
                print(f"💱 Символ: {symbol}")
                print(f"{side_emoji} Сторона: {side.upper()}")
                print(f"📊 Размер: {size}")
                print(f"🎯 Тип: STOP LIMIT")
                print(f"🛑 Цена срабатывания: ${trigger_price}")
                print(f"💰 Лимитная цена: ${limit_price}")
                
                # Детальное объяснение механизма
                print(f"\\n💡 МЕХАНИЗМ СТОП-ЛИМИТ ОРДЕРА:")
                print("1. 🎯 Ожидание достижения стоп-цены")
                if side == "buy":
                    print(f"2. 📈 При росте цены до ${trigger_price} активируется лимитный ордер")
                    print(f"3. 🟢 Покупка по цене не выше ${limit_price}")
                else:
                    print(f"2. 📉 При падении цены до ${trigger_price} активируется лимитный ордер")
                    print(f"3. 🔴 Продажа по цене не ниже ${limit_price}")
                print("4. ⏳ Ордер остается в стакане до исполнения или отмены")
                
                # Анализ цен
                try:
                    trigger_float = float(trigger_price)
                    limit_float = float(limit_price)
                    size_float = float(size)
                    
                    print(f"\\n📊 АНАЛИЗ ЦЕН:")
                    if side == "buy":
                        if limit_float >= trigger_float:
                            print("✅ Логичная настройка: лимит >= стоп")
                        else:
                            print("⚠️ Внимание: лимит < стоп (может не исполниться)")
                    else:
                        if limit_float <= trigger_float:
                            print("✅ Логичная настройка: лимит <= стоп")
                        else:
                            print("⚠️ Внимание: лимит > стоп (может не исполниться)")
                    
                    price_diff = abs(trigger_float - limit_float)
                    price_diff_pct = (price_diff / trigger_float) * 100
                    print(f"📏 Разница цен: ${price_diff:.2f} ({price_diff_pct:.2f}%)")
                    
                    notional = size_float * limit_float
                    print(f"💰 Стоимость позиции: ${notional:,.2f}")
                    
                    if notional > 10000:
                        print(f"🚨 КРУПНАЯ ПОЗИЦИЯ: ${notional:,.2f}")
                        print("⚠️ Убедитесь в достаточной ликвидности!")
                
                except:
                    pass
                
                print(f"\\n⚠️ ПРЕИМУЩЕСТВА СТОП-ЛИМИТ:")
                print("• 🎯 Контроль цены исполнения")
                print("• 💰 Защита от неблагоприятного проскальзывания")
                print("• 📊 Лучшая цена исполнения")
                
                print(f"\\n⚠️ НЕДОСТАТКИ:")
                print("• ⏳ Возможность неисполнения")
                print("• 📈 Риск пропуска движения")
                print("• 🔄 Требует мониторинга")
                
                return data
            else:
                print(f"❌ Ошибка API: {data.get('msg', 'Unknown error')}")
                
                # Детальная обработка ошибок
                error_msg = data.get('msg', '').lower()
                if 'insufficient' in error_msg:
                    print("💡 Проверьте баланс аккаунта")
                elif 'price' in error_msg:
                    print("💡 Проверьте корректность цен")
                elif 'size' in error_msg:
                    print("💡 Проверьте минимальный размер ордера")
                
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


def place_stop_limit_interactive():
    """Интерактивное размещение стоп-лимит ордера"""
    print("🎯 РАЗМЕЩЕНИЕ СТОП-ЛИМИТ ОРДЕРА")
    print("=" * 40)
    
    # Получаем символ
    symbol = input("💱 Введите торговую пару (например, BTCUSDT): ").strip().upper()
    if not symbol:
        print("❌ Торговая пара не указана")
        return None
    
    # Получаем сторону
    print("\\n📊 Выберите сторону:")
    print("1. 🟢 BUY - Покупка (лонг)")
    print("2. 🔴 SELL - Продажа (шорт)")
    
    side_choice = input("Ваш выбор (1-2): ").strip()
    
    if side_choice == "1":
        side = "buy"
    elif side_choice == "2":
        side = "sell"
    else:
        print("❌ Неверный выбор")
        return None
    
    # Получаем размер
    try:
        size = input(f"📊 Введите размер позиции: ").strip()
        size_float = float(size)
        if size_float <= 0:
            print("❌ Размер должен быть больше 0")
            return None
    except ValueError:
        print("❌ Неверный размер")
        return None
    
    # Получаем стоп-цену
    try:
        trigger_price = input(f"🛑 Введите стоп-цену срабатывания ($): ").strip()
        trigger_float = float(trigger_price)
        if trigger_float <= 0:
            print("❌ Стоп-цена должна быть больше 0")
            return None
    except ValueError:
        print("❌ Неверная стоп-цена")
        return None
    
    # Получаем лимитную цену
    try:
        limit_price = input(f"💰 Введите лимитную цену исполнения ($): ").strip()
        limit_float = float(limit_price)
        if limit_float <= 0:
            print("❌ Лимитная цена должна быть больше 0")
            return None
    except ValueError:
        print("❌ Неверная лимитная цена")
        return None
    
    # Проверяем логичность цен
    print(f"\\n🔍 ПРОВЕРКА ЛОГИКИ ЦЕН:")
    if side == "buy":
        if limit_float < trigger_float:
            print("⚠️ ВНИМАНИЕ: Лимит меньше стопа!")
            print("💡 Для BUY обычно лимит >= стоп")
            confirm = input("Продолжить? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y', 'да']:
                return None
    else:
        if limit_float > trigger_float:
            print("⚠️ ВНИМАНИЕ: Лимит больше стопа!")
            print("💡 Для SELL обычно лимит <= стоп")
            confirm = input("Продолжить? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y', 'да']:
                return None
    
    # Клиентский ID (опционально)
    client_oid = input("🆔 Client OID (необязательно): ").strip()
    if not client_oid:
        client_oid = None
    
    # Показываем сводку
    print(f"\\n📋 ПОДТВЕРЖДЕНИЕ ОРДЕРА:")
    print("=" * 35)
    side_emoji = "🟢" if side == "buy" else "🔴"
    print(f"💱 Пара: {symbol}")
    print(f"{side_emoji} Сторона: {side.upper()}")
    print(f"📊 Размер: {size}")
    print(f"🎯 Тип: STOP LIMIT")
    print(f"🛑 Стоп-цена: ${trigger_price}")
    print(f"💰 Лимит-цена: ${limit_price}")
    
    # Расчеты
    try:
        price_diff = abs(trigger_float - limit_float)
        price_diff_pct = (price_diff / trigger_float) * 100
        notional = size_float * limit_float
        
        print(f"\\n📊 РАСЧЕТЫ:")
        print(f"📏 Разница цен: {price_diff_pct:.2f}%")
        print(f"💰 Стоимость: ${notional:,.2f}")
    except:
        pass
    
    # Объяснение логики
    print(f"\\n💡 ЧТО ПРОИЗОЙДЕТ:")
    if side == "buy":
        print(f"1. При росте цены до ${trigger_price} активируется лимитный ордер")
        print(f"2. Покупка произойдет по цене не выше ${limit_price}")
    else:
        print(f"1. При падении цены до ${trigger_price} активируется лимитный ордер")
        print(f"2. Продажа произойдет по цене не ниже ${limit_price}")
    
    confirm = input("\\nПодтвердить размещение? (yes/no): ").strip().lower()
    
    if confirm in ['yes', 'y', 'да']:
        return place_stop_limit_order(symbol, side, size, trigger_price, limit_price, client_oid)
    else:
        print("❌ Размещение отменено")
        return None


def place_bracket_order():
    """Размещение bracket ордера (стоп-лимит + тейк-профит)"""
    print("🎯 BRACKET ОРДЕР (СТОП-ЛИМИТ)")
    print("=" * 40)
    print("💡 Стоп-лимит ордер с автоматической защитой")
    
    symbol = input("💱 Торговая пара: ").strip().upper()
    if not symbol:
        print("❌ Торговая пара не указана")
        return None
    
    print("\\n📊 Выберите стратегию:")
    print("1. 🟢 Лонг breakout (покупка при пробитии)")
    print("2. 🔴 Шорт breakdown (продажа при пробитии)")
    
    choice = input("Ваш выбор (1-2): ").strip()
    
    if choice == "1":
        side = "buy"
        print("\\n🟢 ЛОНГ BREAKOUT СТРАТЕГИЯ:")
        print("• Покупка при пробитии уровня сопротивления")
        print("• Лимитная цена защищает от проскальзывания")
    elif choice == "2":
        side = "sell"
        print("\\n🔴 ШОРТ BREAKDOWN СТРАТЕГИЯ:")
        print("• Продажа при пробитии уровня поддержки")
        print("• Лимитная цена защищает от проскальзывания")
    else:
        print("❌ Неверный выбор")
        return None
    
    try:
        size = input(f"📊 Размер позиции: ").strip()
        
        if side == "buy":
            trigger_price = input(f"📈 Цена пробития вверх (стоп): ").strip()
            limit_price = input(f"💰 Максимальная цена покупки (лимит): ").strip()
        else:
            trigger_price = input(f"📉 Цена пробития вниз (стоп): ").strip()
            limit_price = input(f"💰 Минимальная цена продажи (лимит): ").strip()
        
        print(f"\\n🎯 BRACKET ОРДЕР:")
        print(f"💱 {symbol}")
        print(f"📊 Размер: {size}")
        print(f"🛑 Стоп: ${trigger_price}")
        print(f"💰 Лимит: ${limit_price}")
        
        confirm = input("\\nРазместить bracket ордер? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y', 'да']:
            client_oid = f"bracket_{int(time.time())}"
            return place_stop_limit_order(symbol, side, size, trigger_price, limit_price, client_oid)
        else:
            print("❌ Размещение отменено")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка ввода: {e}")
        return None


def main():
    """Основная функция"""
    print("🎯 BITGET USDT PERP - СТОП-ЛИМИТ ОРДЕРА")
    print("=" * 50)
    
    print("\\n🔌 Выберите режим:")
    print("1. 🎯 Стоп-лимит ордер")
    print("2. 🔍 Интерактивное размещение")
    print("3. 📊 Bracket ордер")
    
    try:
        choice = input("\\nВаш выбор (1-3): ").strip()
        
        if choice == "1":
            symbol = input("💱 Торговая пара: ").strip().upper()
            side = input("📊 Сторона (buy/sell): ").strip().lower()
            size = input("📊 Размер: ").strip()
            trigger_price = input("🛑 Стоп-цена: ").strip()
            limit_price = input("💰 Лимит-цена: ").strip()
            
            if all([symbol, side, size, trigger_price, limit_price]):
                place_stop_limit_order(symbol, side, size, trigger_price, limit_price)
            else:
                print("❌ Не все параметры указаны")
                
        elif choice == "2":
            place_stop_limit_interactive()
            
        elif choice == "3":
            place_bracket_order()
            
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
