#!/usr/bin/env python3
"""
Bitget USDT Perpetual REST API - Place Stop Market Order

Размещение стоп-маркет ордера для фьючерсов.
Ордер исполняется по рыночной цене при достижении стоп-цены.

Документация: https://www.bitget.com/api-doc/contract/trade/Place-Order

Параметры:
- symbol: торговая пара (обязательный)
- side: сторона (buy/sell) 
- size: размер позиции
- triggerPrice: стоп-цена срабатывания
- orderType: stop_market
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


def place_stop_market_order(symbol, side, size, trigger_price, client_oid=None):
    """
    Размещение стоп-маркет ордера
    
    Args:
        symbol (str): Торговая пара (например, BTCUSDT)
        side (str): Сторона (buy/sell)
        size (str): Размер позиции
        trigger_price (str): Стоп-цена срабатывания
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
        client_oid = f"stop_market_{int(time.time())}"
    
    body_data = {
        'symbol': symbol,
        'productType': 'USDT-FUTURES',
        'marginMode': 'crossed',
        'marginCoin': 'USDT',
        'side': side,
        'orderType': 'stop_market',
        'size': str(size),
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
        print(f"🛑 Размещение стоп-маркет ордера...")
        print(f"💱 Пара: {symbol}")
        print(f"{side_emoji} Сторона: {side.upper()}")
        print(f"📊 Размер: {size}")
        print(f"🎯 Стоп-цена: ${trigger_price}")
        print(f"🆔 Client OID: {client_oid}")
        
        response = requests.post(url, headers=headers, data=body)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == '00000':
                order_data = data.get('data', {})
                
                print("\\n✅ Стоп-маркет ордер успешно размещен!")
                print("=" * 50)
                
                # Информация об ордере
                order_id = order_data.get('orderId', 'N/A')
                client_order_id = order_data.get('clientOid', client_oid)
                
                print(f"🆔 ID ордера: {order_id}")
                print(f"👤 Client OID: {client_order_id}")
                print(f"💱 Символ: {symbol}")
                print(f"{side_emoji} Сторона: {side.upper()}")
                print(f"📊 Размер: {size}")
                print(f"🛑 Тип: STOP MARKET")
                print(f"🎯 Цена срабатывания: ${trigger_price}")
                
                # Пояснение механизма
                print(f"\\n💡 МЕХАНИЗМ СТОП-МАРКЕТ ОРДЕРА:")
                if side == "buy":
                    print("🟢 При росте цены до ${} ордер исполнится по рыночной цене".format(trigger_price))
                    print("📈 Используется для входа в лонг при пробитии уровня")
                else:
                    print("🔴 При падении цены до ${} ордер исполнится по рыночной цене".format(trigger_price))
                    print("📉 Используется для входа в шорт при пробитии уровня")
                
                print(f"\\n⚠️ ВАЖНО:")
                print("• Ордер будет исполнен по текущей рыночной цене")
                print("• Возможно проскальзывание цены")
                print("• Контролируйте ликвидность рынка")
                
                # Предупреждения о рисках
                try:
                    size_float = float(size)
                    trigger_float = float(trigger_price)
                    notional = size_float * trigger_float
                    
                    if notional > 10000:  # Большая позиция
                        print(f"\\n🚨 КРУПНАЯ ПОЗИЦИЯ: ${notional:,.2f}")
                        print("⚠️ Убедитесь в достаточной ликвидности!")
                    
                except:
                    pass
                
                return data
            else:
                print(f"❌ Ошибка API: {data.get('msg', 'Unknown error')}")
                
                # Детальная обработка ошибок
                error_msg = data.get('msg', '').lower()
                if 'insufficient' in error_msg:
                    print("💡 Проверьте баланс аккаунта")
                elif 'price' in error_msg:
                    print("💡 Проверьте корректность стоп-цены")
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


def place_stop_market_interactive():
    """Интерактивное размещение стоп-маркет ордера"""
    print("🛑 РАЗМЕЩЕНИЕ СТОП-МАРКЕТ ОРДЕРА")
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
        trigger_price = input(f"🎯 Введите стоп-цену срабатывания ($): ").strip()
        trigger_float = float(trigger_price)
        if trigger_float <= 0:
            print("❌ Стоп-цена должна быть больше 0")
            return None
    except ValueError:
        print("❌ Неверная стоп-цена")
        return None
    
    # Клиентский ID (опционально)
    client_oid = input("🆔 Client OID (необязательно): ").strip()
    if not client_oid:
        client_oid = None
    
    # Показываем сводку и подтверждение
    print(f"\\n📋 ПОДТВЕРЖДЕНИЕ ОРДЕРА:")
    print("=" * 30)
    side_emoji = "🟢" if side == "buy" else "🔴"
    print(f"💱 Пара: {symbol}")
    print(f"{side_emoji} Сторона: {side.upper()}")
    print(f"📊 Размер: {size}")
    print(f"🛑 Тип: STOP MARKET")
    print(f"🎯 Стоп-цена: ${trigger_price}")
    
    # Расчет примерной стоимости
    try:
        notional = size_float * trigger_float
        print(f"💰 Примерная стоимость: ${notional:,.2f}")
    except:
        pass
    
    # Объяснение логики
    print(f"\\n💡 ЛОГИКА ИСПОЛНЕНИЯ:")
    if side == "buy":
        print(f"🟢 Ордер сработает при росте цены до ${trigger_price}")
        print("📈 Будет исполнен по рыночной цене покупки")
    else:
        print(f"🔴 Ордер сработает при падении цены до ${trigger_price}")
        print("📉 Будет исполнен по рыночной цене продажи")
    
    confirm = input("\\nПодтвердить размещение? (yes/no): ").strip().lower()
    
    if confirm in ['yes', 'y', 'да']:
        return place_stop_market_order(symbol, side, size, trigger_price, client_oid)
    else:
        print("❌ Размещение отменено")
        return None


def place_stop_loss_order():
    """Размещение стоп-лосс ордера (защитный стоп)"""
    print("🛡️ РАЗМЕЩЕНИЕ СТОП-ЛОСС ОРДЕРА")
    print("=" * 40)
    
    symbol = input("💱 Торговая пара: ").strip().upper()
    if not symbol:
        print("❌ Торговая пара не указана")
        return None
    
    print("\\n📊 Выберите направление защиты:")
    print("1. 🔴 Защита лонг позиции (SELL стоп)")
    print("2. 🟢 Защита шорт позиции (BUY стоп)")
    
    choice = input("Ваш выбор (1-2): ").strip()
    
    if choice == "1":
        side = "sell"
        print("🔴 Стоп для защиты лонг позиции")
        print("💡 Ордер сработает при падении цены (защита от убытков)")
    elif choice == "2":
        side = "buy"
        print("🟢 Стоп для защиты шорт позиции")
        print("💡 Ордер сработает при росте цены (защита от убытков)")
    else:
        print("❌ Неверный выбор")
        return None
    
    try:
        size = input(f"📊 Размер для закрытия: ").strip()
        trigger_price = input(f"🎯 Стоп-цена защиты ($): ").strip()
        
        # Дополнительное подтверждение для стоп-лосса
        print(f"\\n🛡️ СТОП-ЛОСС ЗАЩИТА:")
        print(f"💱 {symbol}")
        print(f"📊 Размер: {size}")
        print(f"🎯 Цена срабатывания: ${trigger_price}")
        print(f"⚠️ Ордер исполнится по рыночной цене!")
        
        confirm = input("\\nРазместить защитный стоп? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y', 'да']:
            client_oid = f"stop_loss_{int(time.time())}"
            return place_stop_market_order(symbol, side, size, trigger_price, client_oid)
        else:
            print("❌ Размещение отменено")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка ввода: {e}")
        return None


def main():
    """Основная функция"""
    print("🛑 BITGET USDT PERP - СТОП-МАРКЕТ ОРДЕРА")
    print("=" * 50)
    
    print("\\n🔌 Выберите режим:")
    print("1. 🛑 Стоп-маркет ордер")
    print("2. 🔍 Интерактивное размещение")
    print("3. 🛡️ Стоп-лосс (защита)")
    
    try:
        choice = input("\\nВаш выбор (1-3): ").strip()
        
        if choice == "1":
            symbol = input("💱 Торговая пара: ").strip().upper()
            side = input("📊 Сторона (buy/sell): ").strip().lower()
            size = input("📊 Размер: ").strip()
            trigger_price = input("🎯 Стоп-цена: ").strip()
            
            if all([symbol, side, size, trigger_price]):
                place_stop_market_order(symbol, side, size, trigger_price)
            else:
                print("❌ Не все параметры указаны")
                
        elif choice == "2":
            place_stop_market_interactive()
            
        elif choice == "3":
            place_stop_loss_order()
            
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
