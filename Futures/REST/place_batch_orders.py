#!/usr/bin/env python3
"""
Bitget USDT Perpetual REST API - Batch Orders

Размещение пакетных (batch) заявок для фьючерсной торговой пары.
Позволяет разместить несколько заявок одновременно.

Документация: https://www.bitget.com/api-doc/contract/trade/Batch-Orders

Параметры:
- symbol: торговая пара (обязательный)
- orderList: список заявок для размещения
- marginCoin: валюта маржи (USDT)
"""

import requests
import json
import time
import hmac
import hashlib
import base64
from datetime import datetime


def load_config():
    """Загрузка конфигурации из файла"""
    try:
        with open('/Users/timurbogatyrev/Documents/VS Code/Algo/ExchangeAPI/Bitget/config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл config.json не найден!")
        return None


def create_signature(secret_key, message):
    """Создание подписи для аутентификации"""
    return base64.b64encode(
        hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')


def place_batch_orders(symbol="BTCUSDT", order_list=None, margin_coin="USDT"):
    """
    Размещение пакетных заявок для фьючерсов
    
    Args:
        symbol (str): Торговая пара
        order_list (list): Список заявок
        margin_coin (str): Валюта маржи
    
    Returns:
        dict: Ответ API с результатами размещения
    """
    config = load_config()
    if not config:
        return None
    
    # Проверяем наличие API ключей
    if not all(k in config for k in ['apiKey', 'secretKey', 'passPhrase']):
        print("❌ Отсутствуют необходимые API ключи в конфигурации!")
        return None
    
    if not order_list:
        print("❌ Список заявок не может быть пустым!")
        return None
    
    if len(order_list) > 20:
        print("❌ Максимальное количество заявок в пакете: 20")
        return None
    
    # Подготавливаем данные запроса
    timestamp = str(int(time.time() * 1000))
    
    request_data = {
        'symbol': symbol,
        'productType': 'USDT-FUTURES',
        'marginCoin': margin_coin,
        'orderDataList': order_list
    }
    
    body = json.dumps(request_data, separators=(',', ':'))
    
    try:
        # Создаем подпись
        message = timestamp + 'POST' + '/api/v2/mix/order/batch-orders' + body
        signature = create_signature(config['secretKey'], message)
        
        # Заголовки запроса
        headers = {
            'ACCESS-KEY': config['apiKey'],
            'ACCESS-SIGN': signature,
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-PASSPHRASE': config['passPhrase'],
            'Content-Type': 'application/json',
            'locale': 'en-US'
        }
        
        print(f"📦 Размещение пакета из {len(order_list)} заявок для {symbol} FUTURES...")
        
        # Отправляем запрос
        url = f"{config['baseURL']}/api/v2/mix/order/batch-orders"
        response = requests.post(url, headers=headers, data=body)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == '00000':
                result_list = data.get('data', {}).get('orderInfo', [])
                success_list = data.get('data', {}).get('success', [])
                failure_list = data.get('data', {}).get('failure', [])
                
                print(f"✅ Пакетная заявка обработана!")
                print("=" * 80)
                
                # Статистика результатов
                total_orders = len(order_list)
                success_count = len(success_list)
                failure_count = len(failure_list)
                
                print(f"📊 РЕЗУЛЬТАТЫ ПАКЕТНОГО РАЗМЕЩЕНИЯ:")
                print(f"   📦 Всего заявок: {total_orders}")
                print(f"   ✅ Успешно размещено: {success_count}")
                print(f"   ❌ Не удалось разместить: {failure_count}")
                print(f"   📈 Процент успеха: {(success_count/total_orders*100):.1f}%")
                print()
                
                # Показываем успешные заявки
                if success_list:
                    print(f"✅ УСПЕШНО РАЗМЕЩЕННЫЕ ЗАЯВКИ:")
                    print("-" * 80)
                    print(f"{'№':>3} {'Order ID':^20} {'Сторона':^8} {'Размер':>12} {'Цена':>12} {'Тип':^12}")
                    print("-" * 80)
                    
                    for i, success_order in enumerate(success_list, 1):
                        order_id = success_order.get('orderId', 'N/A')
                        client_oid = success_order.get('clientOid', 'N/A')
                        
                        # Ищем соответствующую исходную заявку
                        original_order = None
                        for orig in order_list:
                            if orig.get('clientOid') == client_oid:
                                original_order = orig
                                break
                        
                        if original_order:
                            side = original_order.get('side', 'N/A')
                            size = original_order.get('size', 'N/A')
                            price = original_order.get('price', 'Market')
                            order_type = original_order.get('orderType', 'N/A')
                            
                            # Эмодзи для стороны
                            side_emoji = "🟢" if side == "buy" else "🔴" if side == "sell" else "❓"
                            side_display = f"{side_emoji}{side.upper()}"
                            
                            # Короткий Order ID для отображения
                            short_order_id = order_id[-12:] if len(order_id) > 12 else order_id
                            
                            print(f"{i:>3} {short_order_id:^20} {side_display:^8} {size:>12} {price:>12} {order_type:^12}")
                        else:
                            print(f"{i:>3} {order_id:^20} {'N/A':^8} {'N/A':>12} {'N/A':>12} {'N/A':^12}")
                    
                    print("-" * 80)
                
                # Показываем неудачные заявки
                if failure_list:
                    print(f"\\n❌ НЕУДАЧНЫЕ ЗАЯВКИ:")
                    print("-" * 80)
                    print(f"{'№':>3} {'Client OID':^20} {'Код ошибки':^12} {'Описание ошибки':^30}")
                    print("-" * 80)
                    
                    for i, failure_order in enumerate(failure_list, 1):
                        client_oid = failure_order.get('clientOid', 'N/A')
                        error_code = failure_order.get('errorCode', 'N/A')
                        error_msg = failure_order.get('errorMsg', 'Unknown error')
                        
                        # Сокращаем длинные сообщения
                        if len(error_msg) > 28:
                            error_msg = error_msg[:25] + "..."
                        
                        short_client_oid = client_oid[-12:] if len(client_oid) > 12 else client_oid
                        
                        print(f"{i:>3} {short_client_oid:^20} {error_code:^12} {error_msg:^30}")
                    
                    print("-" * 80)
                
                # Дополнительная информация о заявках
                if result_list:
                    print(f"\\n📋 ДЕТАЛИ РАЗМЕЩЕННЫХ ЗАЯВОК:")
                    print("-" * 100)
                    
                    total_size = 0
                    total_value = 0
                    buy_count = 0
                    sell_count = 0
                    
                    for order_info in result_list:
                        # Извлекаем информацию
                        order_id = order_info.get('orderId', 'N/A')
                        client_oid = order_info.get('clientOid', 'N/A')
                        
                        # Ищем соответствующую исходную заявку для получения параметров
                        original_order = None
                        for orig in order_list:
                            if orig.get('clientOid') == client_oid:
                                original_order = orig
                                break
                        
                        if original_order:
                            side = original_order.get('side', 'unknown')
                            size = float(original_order.get('size', 0))
                            price = float(original_order.get('price', 0)) if original_order.get('price') != 'market' else 0
                            
                            total_size += size
                            if price > 0:
                                total_value += size * price
                            
                            if side == 'buy':
                                buy_count += 1
                            elif side == 'sell':
                                sell_count += 1
                    
                    print(f"📊 Общий размер заявок: {total_size:,.4f} контрактов")
                    if total_value > 0:
                        print(f"💰 Общая стоимость (лимитные): ${total_value:,.2f}")
                    print(f"🟢 Заявки на покупку: {buy_count}")
                    print(f"🔴 Заявки на продажу: {sell_count}")
                
                # Рекомендации
                print(f"\\n💡 РЕКОМЕНДАЦИИ:")
                if success_count == total_orders:
                    print("✅ Все заявки успешно размещены!")
                elif success_count > 0:
                    print(f"⚠️ Частичное размещение. Проверьте причины отклонения {failure_count} заявок")
                    if failure_list:
                        print("   Основные причины отклонения могут быть:")
                        print("   - Недостаточный баланс")
                        print("   - Неверные параметры цены/размера")
                        print("   - Превышение лимитов позиции")
                else:
                    print("❌ Ни одна заявка не была размещена. Проверьте параметры и баланс")
                
                return data
            else:
                print(f"❌ Ошибка API: {data.get('msg', 'Unknown error')}")
                print(f"   Код ошибки: {data.get('code', 'N/A')}")
                return None
        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Сообщение: {error_data.get('msg', response.text)}")
            except:
                print(f"   Ответ: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return None
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return None


def create_batch_orders_interactive():
    """Интерактивное создание пакетных заявок"""
    print("📦 СОЗДАНИЕ ПАКЕТНЫХ ЗАЯВОК (FUTURES)")
    print("=" * 50)
    
    # Получаем торговую пару
    symbol = input("💱 Введите торговую пару (по умолчанию BTCUSDT): ").strip().upper()
    if not symbol:
        symbol = "BTCUSDT"
    
    # Количество заявок
    count_input = input("📊 Количество заявок в пакете (1-20, по умолчанию 3): ").strip()
    try:
        order_count = int(count_input) if count_input else 3
        order_count = max(1, min(20, order_count))
    except ValueError:
        order_count = 3
    
    print(f"\\n📝 Создание {order_count} заявок для {symbol}...")
    print("=" * 50)
    
    order_list = []
    
    for i in range(order_count):
        print(f"\\n📋 ЗАЯВКА #{i+1}:")
        
        # Сторона заявки
        print("🔄 Выберите сторону:")
        print("1. 🟢 Buy (покупка)")
        print("2. 🔴 Sell (продажа)")
        
        side_input = input("Сторона (1-2): ").strip()
        if side_input == "1":
            side = "buy"
            side_display = "🟢 BUY"
        elif side_input == "2":
            side = "sell"
            side_display = "🔴 SELL"
        else:
            side = "buy"
            side_display = "🟢 BUY"
        
        # Тип заявки
        print(f"\\n📊 Выберите тип заявки:")
        print("1. limit - лимитная заявка")
        print("2. market - рыночная заявка")
        
        type_input = input("Тип (1-2): ").strip()
        if type_input == "1":
            order_type = "limit"
            type_display = "Лимитная"
        elif type_input == "2":
            order_type = "market"
            type_display = "Рыночная"
        else:
            order_type = "limit"
            type_display = "Лимитная"
        
        # Размер заявки
        size_input = input(f"📏 Размер заявки в контрактах: ").strip()
        try:
            size = str(float(size_input))
        except ValueError:
            print("❌ Неверный размер, используется 0.01")
            size = "0.01"
        
        # Цена (только для лимитных заявок)
        price = None
        if order_type == "limit":
            price_input = input(f"💰 Цена за контракт (USD): ").strip()
            try:
                price = str(float(price_input))
            except ValueError:
                print("❌ Неверная цена, заявка будет отклонена")
                price = "0"
        
        # Создаем заявку
        order = {
            'symbol': symbol,
            'productType': 'USDT-FUTURES',
            'marginCoin': 'USDT',
            'size': size,
            'side': side,
            'orderType': order_type,
            'clientOid': f"batch_{int(time.time()*1000)}_{i+1}",  # Уникальный ID
            'reduceOnly': 'false'
        }
        
        if order_type == "limit" and price:
            order['price'] = price
        
        order_list.append(order)
        
        # Показываем созданную заявку
        price_display = f"${price}" if price else "Market"
        print(f"✅ Заявка {i+1}: {side_display} {size} контрактов по {price_display} ({type_display})")
    
    print(f"\\n📦 Подготовлено {len(order_list)} заявок. Разместить? (y/n): ", end="")
    confirm = input().strip().lower()
    
    if confirm in ['y', 'yes', 'да', 'д']:
        return place_batch_orders(symbol, order_list)
    else:
        print("❌ Размещение отменено")
        return None


def create_ladder_orders():
    """Создание лестничных заявок"""
    print("🪜 СОЗДАНИЕ ЛЕСТНИЧНЫХ ЗАЯВОК")
    print("=" * 40)
    
    symbol = input("💱 Торговая пара (по умолчанию BTCUSDT): ").strip().upper()
    if not symbol:
        symbol = "BTCUSDT"
    
    # Сторона
    print("\\n🔄 Выберите сторону:")
    print("1. 🟢 Buy (покупка) - лестница снизу")
    print("2. 🔴 Sell (продажа) - лестница сверху")
    
    side_input = input("Сторона (1-2): ").strip()
    if side_input == "1":
        side = "buy"
        side_display = "🟢 BUY"
    elif side_input == "2":
        side = "sell"
        side_display = "🔴 SELL"
    else:
        side = "buy"
        side_display = "🟢 BUY"
    
    # Параметры лестницы
    start_price_input = input(f"💰 Начальная цена лестницы: ").strip()
    try:
        start_price = float(start_price_input)
    except ValueError:
        print("❌ Неверная начальная цена")
        return None
    
    step_input = input(f"📏 Шаг цены (USD): ").strip()
    try:
        price_step = float(step_input)
    except ValueError:
        print("❌ Неверный шаг цены")
        return None
    
    levels_input = input(f"🪜 Количество уровней (1-20): ").strip()
    try:
        levels = int(levels_input)
        levels = max(1, min(20, levels))
    except ValueError:
        levels = 5
    
    size_input = input(f"📊 Размер каждой заявки (контракты): ").strip()
    try:
        size_per_level = float(size_input)
    except ValueError:
        print("❌ Неверный размер заявки")
        return None
    
    print(f"\\n🪜 СОЗДАНИЕ ЛЕСТНИЦЫ {side_display}:")
    print(f"   📍 Начальная цена: ${start_price:.4f}")
    print(f"   📏 Шаг: ${price_step:.4f}")
    print(f"   🪜 Уровней: {levels}")
    print(f"   📊 Размер каждого: {size_per_level} контрактов")
    print(f"   💰 Общий размер: {size_per_level * levels} контрактов")
    
    # Создаем лестницу заявок
    order_list = []
    total_value = 0
    
    print(f"\\n📋 СТРУКТУРА ЛЕСТНИЦЫ:")
    print(f"{'№':>3} {'Цена':>12} {'Размер':>12} {'Сумма':>12}")
    print("-" * 45)
    
    for i in range(levels):
        if side == "buy":
            # Для покупки цены идут вниз
            current_price = start_price - (price_step * i)
        else:
            # Для продажи цены идут вверх
            current_price = start_price + (price_step * i)
        
        order_value = current_price * size_per_level
        total_value += order_value
        
        print(f"{i+1:>3} ${current_price:>11.4f} {size_per_level:>12.4f} ${order_value:>11.2f}")
        
        # Создаем заявку
        order = {
            'symbol': symbol,
            'productType': 'USDT-FUTURES',
            'marginCoin': 'USDT',
            'size': str(size_per_level),
            'side': side,
            'orderType': 'limit',
            'price': str(current_price),
            'clientOid': f"ladder_{int(time.time()*1000)}_{i+1}",
            'reduceOnly': 'false'
        }
        
        order_list.append(order)
    
    print("-" * 45)
    print(f"💰 Общая стоимость лестницы: ${total_value:,.2f}")
    
    print(f"\\n🪜 Разместить лестницу из {levels} заявок? (y/n): ", end="")
    confirm = input().strip().lower()
    
    if confirm in ['y', 'yes', 'да', 'д']:
        return place_batch_orders(symbol, order_list)
    else:
        print("❌ Размещение лестницы отменено")
        return None


def create_grid_orders():
    """Создание сетки заявок"""
    print("🕸️ СОЗДАНИЕ СЕТКИ ЗАЯВОК")
    print("=" * 35)
    
    symbol = input("💱 Торговая пара (по умолчанию BTCUSDT): ").strip().upper()
    if not symbol:
        symbol = "BTCUSDT"
    
    # Центральная цена
    center_price_input = input(f"🎯 Центральная цена сетки: ").strip()
    try:
        center_price = float(center_price_input)
    except ValueError:
        print("❌ Неверная центральная цена")
        return None
    
    # Параметры сетки
    grid_step_input = input(f"📏 Шаг сетки (%): ").strip()
    try:
        grid_step_pct = float(grid_step_input) / 100
    except ValueError:
        grid_step_pct = 0.01  # 1% по умолчанию
    
    levels_each_input = input(f"🕸️ Уровней в каждую сторону (1-10): ").strip()
    try:
        levels_each = int(levels_each_input)
        levels_each = max(1, min(10, levels_each))
    except ValueError:
        levels_each = 3
    
    size_input = input(f"📊 Размер каждой заявки (контракты): ").strip()
    try:
        size_per_order = float(size_input)
    except ValueError:
        print("❌ Неверный размер заявки")
        return None
    
    total_orders = levels_each * 2  # По levels_each в каждую сторону
    
    if total_orders > 20:
        print(f"❌ Слишком много заявок ({total_orders}). Максимум 20")
        return None
    
    print(f"\\n🕸️ СОЗДАНИЕ СЕТКИ:")
    print(f"   🎯 Центральная цена: ${center_price:.4f}")
    print(f"   📏 Шаг сетки: {grid_step_pct*100:.2f}%")
    print(f"   🕸️ Уровней: {levels_each} покупок + {levels_each} продаж = {total_orders}")
    print(f"   📊 Размер каждой: {size_per_order} контрактов")
    
    # Создаем сетку заявок
    order_list = []
    buy_orders = []
    sell_orders = []
    
    print(f"\\n📋 СТРУКТУРА СЕТКИ:")
    print(f"{'Тип':^8} {'Цена':>12} {'Размер':>12} {'% от центра':>12}")
    print("-" * 50)
    
    # Заявки на покупку (ниже центральной цены)
    for i in range(1, levels_each + 1):
        buy_price = center_price * (1 - grid_step_pct * i)
        price_diff_pct = -grid_step_pct * i * 100
        
        print(f"{'🟢 BUY':^8} ${buy_price:>11.4f} {size_per_order:>12.4f} {price_diff_pct:>11.2f}%")
        
        order = {
            'symbol': symbol,
            'productType': 'USDT-FUTURES',
            'marginCoin': 'USDT',
            'size': str(size_per_order),
            'side': 'buy',
            'orderType': 'limit',
            'price': str(buy_price),
            'clientOid': f"grid_buy_{int(time.time()*1000)}_{i}",
            'reduceOnly': 'false'
        }
        
        buy_orders.append(order)
        order_list.append(order)
    
    # Заявки на продажу (выше центральной цены)
    for i in range(1, levels_each + 1):
        sell_price = center_price * (1 + grid_step_pct * i)
        price_diff_pct = grid_step_pct * i * 100
        
        print(f"{'🔴 SELL':^8} ${sell_price:>11.4f} {size_per_order:>12.4f} {price_diff_pct:>11.2f}%")
        
        order = {
            'symbol': symbol,
            'productType': 'USDT-FUTURES',
            'marginCoin': 'USDT',
            'size': str(size_per_order),
            'side': 'sell',
            'orderType': 'limit',
            'price': str(sell_price),
            'clientOid': f"grid_sell_{int(time.time()*1000)}_{i}",
            'reduceOnly': 'false'
        }
        
        sell_orders.append(order)
        order_list.append(order)
    
    print("-" * 50)
    
    # Расчет требуемого баланса
    total_buy_value = sum(float(order['price']) * float(order['size']) for order in buy_orders)
    print(f"💰 Требуемый баланс для покупок: ${total_buy_value:,.2f}")
    print(f"📊 Общий размер сетки: {size_per_order * total_orders} контрактов")
    
    print(f"\\n🕸️ Разместить сетку из {total_orders} заявок? (y/n): ", end="")
    confirm = input().strip().lower()
    
    if confirm in ['y', 'yes', 'да', 'д']:
        return place_batch_orders(symbol, order_list)
    else:
        print("❌ Размещение сетки отменено")
        return None


def create_dca_orders():
    """Создание DCA (Dollar Cost Averaging) заявок"""
    print("💸 СОЗДАНИЕ DCA ЗАЯВОК")
    print("=" * 30)
    
    symbol = input("💱 Торговая пара (по умолчанию BTCUSDT): ").strip().upper()
    if not symbol:
        symbol = "BTCUSDT"
    
    # Сторона (обычно DCA для покупок)
    print("\\n🔄 Выберите сторону:")
    print("1. 🟢 Buy DCA (усреднение покупок)")
    print("2. 🔴 Sell DCA (усреднение продаж)")
    
    side_input = input("Сторона (1-2): ").strip()
    if side_input == "1":
        side = "buy"
        side_display = "🟢 BUY DCA"
    elif side_input == "2":
        side = "sell"
        side_display = "🔴 SELL DCA"
    else:
        side = "buy"
        side_display = "🟢 BUY DCA"
    
    # Общая сумма для DCA
    total_amount_input = input(f"💰 Общая сумма для DCA (USD): ").strip()
    try:
        total_amount = float(total_amount_input)
    except ValueError:
        print("❌ Неверная сумма")
        return None
    
    # Количество частей
    parts_input = input(f"📊 На сколько частей разделить (2-20): ").strip()
    try:
        parts = int(parts_input)
        parts = max(2, min(20, parts))
    except ValueError:
        parts = 5
    
    # Текущая цена для расчета
    current_price_input = input(f"🎯 Текущая рыночная цена: ").strip()
    try:
        current_price = float(current_price_input)
    except ValueError:
        print("❌ Неверная текущая цена")
        return None
    
    # Диапазон цен для DCA
    if side == "buy":
        print("📉 Для DCA покупок укажите диапазон ниже текущей цены")
        max_price = current_price * 0.95  # По умолчанию -5%
        min_price = current_price * 0.80  # По умолчанию -20%
    else:
        print("📈 Для DCA продаж укажите диапазон выше текущей цены")
        min_price = current_price * 1.05  # По умолчанию +5%
        max_price = current_price * 1.20  # По умолчанию +20%
    
    max_price_input = input(f"💰 Максимальная цена диапазона (по умолчанию {max_price:.2f}): ").strip()
    if max_price_input:
        try:
            max_price = float(max_price_input)
        except ValueError:
            pass
    
    min_price_input = input(f"💰 Минимальная цена диапазона (по умолчанию {min_price:.2f}): ").strip()
    if min_price_input:
        try:
            min_price = float(min_price_input)
        except ValueError:
            pass
    
    # Проверяем корректность диапазона
    if max_price <= min_price:
        print("❌ Максимальная цена должна быть больше минимальной")
        return None
    
    amount_per_part = total_amount / parts
    price_step = (max_price - min_price) / (parts - 1)
    
    print(f"\\n💸 СОЗДАНИЕ DCA {side_display}:")
    print(f"   💰 Общая сумма: ${total_amount:,.2f}")
    print(f"   📊 Частей: {parts}")
    print(f"   💵 Сумма на часть: ${amount_per_part:,.2f}")
    print(f"   📏 Диапазон цен: ${min_price:.2f} - ${max_price:.2f}")
    print(f"   📈 Шаг цены: ${price_step:.2f}")
    
    # Создаем DCA заявки
    order_list = []
    
    print(f"\\n📋 СТРУКТУРА DCA:")
    print(f"{'№':>3} {'Цена':>12} {'Размер':>12} {'Сумма':>12}")
    print("-" * 45)
    
    for i in range(parts):
        # Рассчитываем цену для этой части
        if side == "buy":
            # Для покупок начинаем с максимальной цены и идем вниз
            order_price = max_price - (price_step * i)
        else:
            # Для продаж начинаем с минимальной цены и идем вверх
            order_price = min_price + (price_step * i)
        
        # Рассчитываем размер в контрактах
        size_contracts = amount_per_part / order_price
        
        print(f"{i+1:>3} ${order_price:>11.2f} {size_contracts:>12.4f} ${amount_per_part:>11.2f}")
        
        # Создаем заявку
        order = {
            'symbol': symbol,
            'productType': 'USDT-FUTURES',
            'marginCoin': 'USDT',
            'size': str(size_contracts),
            'side': side,
            'orderType': 'limit',
            'price': str(order_price),
            'clientOid': f"dca_{side}_{int(time.time()*1000)}_{i+1}",
            'reduceOnly': 'false'
        }
        
        order_list.append(order)
    
    print("-" * 45)
    print(f"💰 Общая сумма DCA: ${total_amount:,.2f}")
    
    print(f"\\n💸 Разместить DCA из {parts} заявок? (y/n): ", end="")
    confirm = input().strip().lower()
    
    if confirm in ['y', 'yes', 'да', 'д']:
        return place_batch_orders(symbol, order_list)
    else:
        print("❌ Размещение DCA отменено")
        return None


def main():
    """Основная функция"""
    print("📦 BITGET FUTURES - ПАКЕТНЫЕ ЗАЯВКИ")
    print("=" * 50)
    
    print("\\n🔌 Выберите режим:")
    print("1. 📦 Пакетные заявки")
    print("2. 🔍 Интерактивное создание")
    print("3. 🪜 Лестничные заявки")
    print("4. 🕸️ Сетка заявок")
    print("5. 💸 DCA заявки")
    
    try:
        choice = input("\\nВаш выбор (1-5): ").strip()
        
        if choice == "1":
            # Пример простых пакетных заявок
            sample_orders = [
                {
                    'symbol': 'BTCUSDT',
                    'productType': 'USDT-FUTURES',
                    'marginCoin': 'USDT',
                    'size': '0.01',
                    'side': 'buy',
                    'orderType': 'limit',
                    'price': '30000',
                    'clientOid': f"batch_sample_{int(time.time()*1000)}_1",
                    'reduceOnly': 'false'
                }
            ]
            place_batch_orders("BTCUSDT", sample_orders)
        elif choice == "2":
            create_batch_orders_interactive()
        elif choice == "3":
            create_ladder_orders()
        elif choice == "4":
            create_grid_orders()
        elif choice == "5":
            create_dca_orders()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
