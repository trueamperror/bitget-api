# -*- coding: utf-8 -*-
"""
Bitget Spot REST API - Place Order (Create Order)
Размещение ордеров

Документация: https://www.bitget.com/api-doc/spot/trade/Place-Order

Описание:
Этот скрипт размещает ордера на спот рынке Bitget.
Поддерживает лимитные и рыночные ордера, а также различные стратегии исполнения.

Параметры:
- symbol: торговая пара (обязательно, например BTCUSDT)
- side: направление (buy/sell)
- orderType: тип ордера (limit/market)
- force: стратегия исполнения (gtc/post_only/fok/ioc)
- price: цена (для лимитных ордеров)
- size: количество
- clientOid: пользовательский ID ордера (опционально)
- triggerPrice: цена срабатывания для TP/SL ордеров
- tpslType: тип ордера (normal/tpsl)

Стратегии исполнения:
- gtc: Good Till Cancelled (до отмены)
- post_only: Только мейкер
- fok: Fill Or Kill (исполнить полностью или отменить)
- ioc: Immediate Or Cancel (исполнить частично, остаток отменить)

ВНИМАНИЕ: Этот скрипт размещает реальные ордера на бирже!
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
        method (str): HTTP метод
        request_path (str): Путь запроса
        query_string (str): Строка запроса
        body (str): Тело запроса
    
    Returns:
        str: Base64 подпись
    """
    
    if query_string:
        message = f"{timestamp}{method.upper()}{request_path}?{query_string}{body}"
    else:
        message = f"{timestamp}{method.upper()}{request_path}{body}"
    
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    return base64.b64encode(signature).decode('utf-8')

def place_order(symbol, side, order_type, size, price=None, force="gtc", client_oid=None, 
                trigger_price=None, tpsl_type="normal"):
    """
    Размещение ордера
    
    Args:
        symbol (str): Торговая пара (например, BTCUSDT)
        side (str): Направление (buy/sell)
        order_type (str): Тип ордера (limit/market)
        size (str): Количество
        price (str): Цена (для лимитных ордеров)
        force (str): Стратегия исполнения
        client_oid (str): Пользовательский ID ордера
        trigger_price (str): Цена срабатывания
        tpsl_type (str): Тип ордера (normal/tpsl)
    
    Returns:
        dict: Результат размещения ордера или None при ошибке
    """
    
    # Проверяем наличие API ключей
    if not API_KEY or not SECRET_KEY or not PASSPHRASE:
        print("❌ API ключи не настроены в конфигурации")
        return None
    
    # Проверяем обязательные параметры
    if not symbol or not side or not order_type or not size:
        print("❌ Не указаны обязательные параметры")
        return None
    
    # Проверяем цену для лимитных ордеров
    if order_type == "limit" and not price:
        print("❌ Для лимитного ордера необходимо указать цену")
        return None
    
    # Формируем тело запроса
    order_data = {
        "symbol": symbol,
        "side": side,
        "orderType": order_type,
        "size": size,
        "tpslType": tpsl_type
    }
    
    # Добавляем опциональные параметры
    if order_type == "limit":
        order_data["force"] = force
        order_data["price"] = price
    
    if client_oid:
        order_data["clientOid"] = client_oid
    
    if trigger_price and tpsl_type == "tpsl":
        order_data["triggerPrice"] = trigger_price
    
    # Путь запроса
    request_path = "/api/v2/spot/trade/place-order"
    
    # Подготовка для подписи
    timestamp = str(int(time.time() * 1000))
    method = "POST"
    body = json.dumps(order_data)
    query_string = ""
    
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
    
    # Формируем URL
    url = f"{BASE_URL}{request_path}"
    
    try:
        print(f"📝 Размещение ордера...")
        print(f"💱 Пара: {symbol}")
        print(f"📊 Сторона: {side.upper()}")
        print(f"📋 Тип: {order_type.upper()}")
        print(f"📦 Количество: {size}")
        if price:
            print(f"💰 Цена: {price}")
        print(f"⚡ Стратегия: {force}")
        
        # Выполняем запрос
        response = requests.post(url, headers=headers, data=body, timeout=10)
        
        # Проверяем статус ответа
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем код ответа Bitget
            if data.get('code') == '00000':
                order_result = data.get('data')
                if order_result:
                    print(f"✅ Ордер успешно размещен")
                    return order_result
                else:
                    print("⚠️ Ордер размещен, но данные не получены")
                    return {}
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

def format_order_response(order_result, order_params):
    """
    Форматирование ответа размещения ордера
    
    Args:
        order_result (dict): Результат размещения ордера
        order_params (dict): Параметры ордера
    """
    
    if not order_result:
        print("📋 Нет данных для отображения")
        return
    
    print(f"\\n📝 ОРДЕР УСПЕШНО РАЗМЕЩЕН")
    print("=" * 60)
    
    # Основная информация
    order_id = order_result.get('orderId', 'N/A')
    client_oid = order_result.get('clientOid', 'N/A')
    
    print(f"🆔 ID ордера: {order_id}")
    if client_oid != 'N/A':
        print(f"🏷️ Клиентский ID: {client_oid}")
    
    # Параметры ордера
    print(f"\\n📋 ПАРАМЕТРЫ ОРДЕРА:")
    print("-" * 30)
    print(f"💱 Торговая пара: {order_params.get('symbol', 'N/A')}")
    print(f"📊 Направление: {order_params.get('side', 'N/A').upper()}")
    print(f"📋 Тип ордера: {order_params.get('orderType', 'N/A').upper()}")
    print(f"📦 Количество: {order_params.get('size', 'N/A')}")
    
    if order_params.get('price'):
        print(f"💰 Цена: {order_params.get('price')}")
    
    if order_params.get('force'):
        print(f"⚡ Стратегия: {order_params.get('force')}")
    
    # Временная метка
    print(f"⏰ Время размещения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Расчет примерной суммы ордера
    try:
        size = float(order_params.get('size', 0))
        if order_params.get('price'):
            price = float(order_params.get('price', 0))
            total_amount = size * price
            print(f"💵 Примерная сумма: {total_amount:.6f}")
    except (ValueError, TypeError):
        pass

def get_current_price(symbol):
    """
    Получение текущей цены для расчетов
    
    Args:
        symbol (str): Торговая пара
    
    Returns:
        float: Текущая цена или None
    """
    
    try:
        endpoint = f"{BASE_URL}/api/v2/spot/market/ticker"
        params = {'symbol': symbol}
        
        response = requests.get(endpoint, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '00000':
                ticker_data = data.get('data')
                if ticker_data:
                    return float(ticker_data.get('close', 0))
        
        return None
        
    except Exception:
        return None

def validate_order_params(symbol, side, order_type, size, price=None):
    """
    Валидация параметров ордера
    
    Args:
        symbol (str): Торговая пара
        side (str): Направление
        order_type (str): Тип ордера
        size (str): Количество
        price (str): Цена
    
    Returns:
        tuple: (is_valid, error_message)
    """
    
    # Проверяем направление
    if side not in ['buy', 'sell']:
        return False, "Направление должно быть 'buy' или 'sell'"
    
    # Проверяем тип ордера
    if order_type not in ['limit', 'market']:
        return False, "Тип ордера должен быть 'limit' или 'market'"
    
    # Проверяем количество
    try:
        size_float = float(size)
        if size_float <= 0:
            return False, "Количество должно быть положительным числом"
    except (ValueError, TypeError):
        return False, "Количество должно быть числом"
    
    # Проверяем цену для лимитных ордеров
    if order_type == 'limit':
        if not price:
            return False, "Для лимитного ордера необходимо указать цену"
        
        try:
            price_float = float(price)
            if price_float <= 0:
                return False, "Цена должна быть положительным числом"
        except (ValueError, TypeError):
            return False, "Цена должна быть числом"
    
    return True, "OK"

def main():
    """Основная функция"""
    print("📝 Bitget Spot REST API - Place Order")
    print("=" * 55)
    
    # ВНИМАНИЕ: Реальный ордер!
    print("\\n🚨 ВНИМАНИЕ: РЕАЛЬНОЕ РАЗМЕЩЕНИЕ ОРДЕРА! 🚨")
    print("=" * 50)
    print("⚠️  Этот скрипт размещает реальный ордер на бирже!")
    print("⚠️  Убедитесь в правильности всех параметров!")
    print("⚠️  Рекомендуется тестировать на небольших суммах!")
    
    # Параметры ордера (ИЗМЕНИТЕ ПОД СВОИ НУЖДЫ)
    symbol = "BTCUSDT"
    side = "buy"  # buy или sell
    order_type = "limit"  # limit или market
    size = "0.001"  # Очень маленькое количество для теста
    price = "30000"  # Цена ниже рыночной для безопасности
    force = "gtc"  # gtc, post_only, fok, ioc
    
    print(f"\\n📋 ПАРАМЕТРЫ ТЕСТОВОГО ОРДЕРА:")
    print("-" * 40)
    print(f"💱 Торговая пара: {symbol}")
    print(f"📊 Направление: {side.upper()}")
    print(f"📋 Тип ордера: {order_type.upper()}")
    print(f"📦 Количество: {size}")
    if order_type == "limit":
        print(f"💰 Цена: {price}")
        print(f"⚡ Стратегия: {force}")
    
    # Получаем текущую цену для справки
    current_price = get_current_price(symbol)
    if current_price:
        print(f"📊 Текущая рыночная цена: {current_price:.2f}")
        
        if order_type == "limit" and price:
            try:
                price_diff = ((float(price) - current_price) / current_price) * 100
                print(f"📊 Отклонение от рынка: {price_diff:+.2f}%")
            except:
                pass
    
    # Валидация параметров
    is_valid, error_msg = validate_order_params(symbol, side, order_type, size, price)
    if not is_valid:
        print(f"❌ Ошибка валидации: {error_msg}")
        return
    
    print(f"✅ Параметры ордера прошли валидацию")
    
    # Запрашиваем подтверждение
    print(f"\\n❓ Подтвердите размещение ордера:")
    confirmation = input("Введите 'РАЗМЕСТИТЬ' для подтверждения: ").strip()
    
    if confirmation != 'РАЗМЕСТИТЬ':
        print("❌ Размещение ордера отменено")
        return
    
    # Генерируем клиентский ID
    client_oid = f"bitget_test_{int(time.time())}"
    
    # Собираем параметры
    order_params = {
        'symbol': symbol,
        'side': side,
        'orderType': order_type,
        'size': size,
        'force': force
    }
    
    if order_type == "limit":
        order_params['price'] = price
    
    # Размещаем ордер
    result = place_order(
        symbol=symbol,
        side=side,
        order_type=order_type,
        size=size,
        price=price if order_type == "limit" else None,
        force=force,
        client_oid=client_oid
    )
    
    # Обрабатываем результат
    if result is not None:
        format_order_response(result, order_params)
        
        # Информация о дальнейших действиях
        print(f"\\n💡 ДАЛЬНЕЙШИЕ ДЕЙСТВИЯ:")
        print("-" * 30)
        print("📋 Проверьте статус ордера через get_orders.py")
        print("🗑️ При необходимости отмените ордер через cancel_order.py")
        print("📊 Мониторьте исполнение через WebSocket")
        
        if result.get('orderId'):
            print(f"\\n🆔 ID ордера для операций: {result.get('orderId')}")
    else:
        print("❌ Не удалось разместить ордер")
        print("\\n🔍 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
        print("- Недостаточный баланс")
        print("- Неверные параметры ордера")
        print("- Торговая пара не активна")
        print("- API ключи не имеют торговых прав")
        print("- Нарушены лимиты биржи")

if __name__ == "__main__":
    main()
