#!/usr/bin/env python3
"""
Bitget USDT Perpetual REST API - Place Stop Loss Order

Размещение стоп-лосс заявки для фьючерсной торговой пары.
Стоп-лосс помогает ограничить потери при неблагоприятном движении цены.

Документация: https://www.bitget.com/api-doc/contract/trade/Place-Stop-Order

Параметры:
- symbol: торговая пара (обязательный)
- side: сторона заявки (buy/sell)
- size: размер позиции для закрытия
- triggerPrice: цена активации стоп-лосса
- executePrice: цена исполнения (для limit) или 'market'
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
        with open('../../config.json', 'r') as f:
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


def place_stop_loss_order(symbol="BTCUSDT", side="sell", size="0.01", trigger_price=None, 
                         execute_price="market", order_type="market", margin_coin="USDT"):
    """
    Размещение стоп-лосс заявки
    
    Args:
        symbol (str): Торговая пара
        side (str): Сторона заявки (buy/sell)
        size (str): Размер в контрактах
        trigger_price (str): Цена активации стоп-лосса
        execute_price (str): Цена исполнения или 'market'
        order_type (str): Тип заявки ('market' или 'limit')
        margin_coin (str): Валюта маржи
    
    Returns:
        dict: Ответ API с результатом размещения
    """
    config = load_config()
    if not config:
        return None
    
    # Проверяем наличие API ключей
    if not all(k in config for k in ['apiKey', 'secretKey', 'passphrase']):
        print("❌ Отсутствуют необходимые API ключи в конфигурации!")
        return None
    
    if not trigger_price:
        print("❌ Цена активации стоп-лосса обязательна!")
        return None
    
    # Подготавливаем данные запроса
    timestamp = str(int(time.time() * 1000))
    
    request_data = {
        'symbol': symbol,
        'productType': 'USDT-FUTURES',
        'marginMode': 'crossed',
        'marginCoin': margin_coin,
        'size': size,
        'side': side,
        'orderType': order_type,
        'triggerPrice': trigger_price,
        'planType': 'normal_plan',  # Обычный план-ордер
        'clientOid': f"stop_loss_{int(time.time()*1000)}"
    }
    
    # Добавляем цену исполнения
    if order_type == "limit" and execute_price != "market":
        request_data['executePrice'] = execute_price
        request_data['triggerType'] = 'fill_price'  # Исполнение по лимитной цене
    else:
        request_data['triggerType'] = 'mark_price'  # Исполнение по рыночной цене
    
    body = json.dumps(request_data, separators=(',', ':'))
    
    try:
        # Создаем подпись
        message = timestamp + 'POST' + '/api/v2/mix/order/place-plan-order' + body
        signature = create_signature(config['secretKey'], message)
        
        # Заголовки запроса
        headers = {
            'ACCESS-KEY': config['apiKey'],
            'ACCESS-SIGN': signature,
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-PASSPHRASE': config['passphrase'],
            'Content-Type': 'application/json',
            'locale': 'en-US'
        }
        
        print(f"🛡️ Размещение стоп-лосс заявки для {symbol} FUTURES...")
        
        # Отправляем запрос
        url = f"{config['baseURL']}/api/v2/mix/order/place-plan-order"
        response = requests.post(url, headers=headers, data=body)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == '00000':
                order_info = data.get('data', {})
                order_id = order_info.get('orderId', 'N/A')
                client_oid = order_info.get('clientOid', 'N/A')
                
                print(f"✅ Стоп-лосс заявка успешно размещена!")
                print("=" * 70)
                
                # Информация о заявке
                print(f"📋 ДЕТАЛИ СТОП-ЛОСС ЗАЯВКИ:")
                print(f"   🆔 Order ID: {order_id}")
                print(f"   📱 Client OID: {client_oid}")
                print(f"   💱 Символ: {symbol}")
                print(f"   🔄 Сторона: {'🟢 BUY' if side == 'buy' else '🔴 SELL'}")
                print(f"   📊 Размер: {size} контрактов")
                print(f"   🚨 Цена активации: ${trigger_price}")
                
                if order_type == "limit" and execute_price != "market":
                    print(f"   💰 Цена исполнения: ${execute_price} (лимитная)")
                else:
                    print(f"   💰 Цена исполнения: Рыночная")
                
                print(f"   💼 Маржинальная валюта: {margin_coin}")
                print(f"   ⏰ Время размещения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Расчет потенциальных потерь
                try:
                    trigger_price_float = float(trigger_price)
                    size_float = float(size)
                    
                    # Примерная позиция (нужна текущая цена для точного расчета)
                    print(f"\\n📊 АНАЛИЗ СТОП-ЛОССА:")
                    print(f"   🎯 При активации на ${trigger_price_float:.4f}")
                    print(f"   📏 Будет закрыто {size_float} контрактов")
                    
                    # Рекомендации
                    print(f"\\n💡 РЕКОМЕНДАЦИИ:")
                    print(f"   ✅ Стоп-лосс активируется автоматически")
                    print(f"   ⚠️ Следите за рыночными условиями")
                    print(f"   📈 Рассмотрите трейлинг стоп для растущих позиций")
                    
                    if order_type == "market":
                        print(f"   🚨 Рыночное исполнение может отличаться от цены активации")
                    else:
                        print(f"   💰 Лимитное исполнение гарантирует цену ${execute_price}")
                
                except ValueError:
                    pass
                
                return data
            else:
                print(f"❌ Ошибка API: {data.get('msg', 'Unknown error')}")
                print(f"   Код ошибки: {data.get('code', 'N/A')}")
                
                # Расшифровка популярных ошибок
                error_code = data.get('code', '')
                if error_code == '40001':
                    print("   💡 Проверьте параметры заявки")
                elif error_code == '40002':
                    print("   💡 Недостаточный баланс")
                elif error_code == '40003':
                    print("   💡 Неверная торговая пара")
                elif error_code == '40004':
                    print("   💡 Превышен лимит заявок")
                
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


def place_stop_loss_interactive():
    """Интерактивное размещение стоп-лосса"""
    print("🛡️ РАЗМЕЩЕНИЕ СТОП-ЛОСС ЗАЯВКИ")
    print("=" * 45)
    
    # Получаем торговую пару
    symbol = input("💱 Введите торговую пару (по умолчанию BTCUSDT): ").strip().upper()
    if not symbol:
        symbol = "BTCUSDT"
    
    # Сторона заявки
    print("\\n🔄 Для закрытия позиции выберите ПРОТИВОПОЛОЖНУЮ сторону:")
    print("1. 🟢 Buy (для закрытия SHORT позиции)")
    print("2. 🔴 Sell (для закрытия LONG позиции)")
    
    side_input = input("Сторона (1-2): ").strip()
    if side_input == "1":
        side = "buy"
        side_display = "🟢 BUY (закрытие SHORT)"
        position_type = "SHORT"
    elif side_input == "2":
        side = "sell"
        side_display = "🔴 SELL (закрытие LONG)"
        position_type = "LONG"
    else:
        side = "sell"
        side_display = "🔴 SELL (закрытие LONG)"
        position_type = "LONG"
    
    # Размер позиции
    size_input = input(f"📊 Размер позиции для закрытия (контракты): ").strip()
    try:
        size = str(float(size_input))
    except ValueError:
        print("❌ Неверный размер, используется 0.01")
        size = "0.01"
    
    # Цена активации стоп-лосса
    trigger_price_input = input(f"🚨 Цена активации стоп-лосса: ").strip()
    try:
        trigger_price = str(float(trigger_price_input))
        trigger_price_float = float(trigger_price)
    except ValueError:
        print("❌ Неверная цена активации")
        return None
    
    # Тип исполнения
    print(f"\\n💰 Выберите тип исполнения:")
    print("1. Market - рыночная цена (быстрое исполнение)")
    print("2. Limit - лимитная цена (контроль цены)")
    
    exec_type_input = input("Тип исполнения (1-2): ").strip()
    if exec_type_input == "2":
        order_type = "limit"
        
        # Цена исполнения для лимитной заявки
        if position_type == "LONG":
            suggested_price = trigger_price_float * 0.999  # Чуть ниже цены активации
            print(f"💡 Для LONG позиции цена исполнения должна быть ниже цены активации")
        else:
            suggested_price = trigger_price_float * 1.001  # Чуть выше цены активации
            print(f"💡 Для SHORT позиции цена исполнения должна быть выше цены активации")
        
        execute_price_input = input(f"💰 Цена исполнения (предлагается ${suggested_price:.4f}): ").strip()
        if execute_price_input:
            try:
                execute_price = str(float(execute_price_input))
            except ValueError:
                execute_price = str(suggested_price)
        else:
            execute_price = str(suggested_price)
    else:
        order_type = "market"
        execute_price = "market"
    
    # Показываем сводку
    print(f"\\n🛡️ СВОДКА СТОП-ЛОСС ЗАЯВКИ:")
    print("=" * 50)
    print(f"💱 Торговая пара: {symbol}")
    print(f"🔄 Тип позиции: {position_type}")
    print(f"📊 Действие: {side_display}")
    print(f"📏 Размер: {size} контрактов")
    print(f"🚨 Цена активации: ${trigger_price}")
    if order_type == "limit":
        print(f"💰 Цена исполнения: ${execute_price} (лимитная)")
    else:
        print(f"💰 Цена исполнения: Рыночная")
    
    # Предупреждения
    print(f"\\n⚠️ ВАЖНЫЕ ПРЕДУПРЕЖДЕНИЯ:")
    if position_type == "LONG":
        print(f"   📉 Стоп-лосс сработает если цена УПАДЕТ до ${trigger_price}")
        if float(trigger_price) > 50000:  # Примерная проверка для BTC
            print(f"   🔍 Проверьте - цена активации не слишком высока?")
    else:
        print(f"   📈 Стоп-лосс сработает если цена ВЫРАСТЕТ до ${trigger_price}")
        if float(trigger_price) < 30000:  # Примерная проверка для BTC
            print(f"   🔍 Проверьте - цена активации не слишком низка?")
    
    print(f"   🛡️ Это заявка для ЗАКРЫТИЯ позиции, а не открытия")
    print(f"   ⚡ Исполнение может отличаться от цены активации при высокой волатильности")
    
    # Подтверждение
    print(f"\\n🛡️ Разместить стоп-лосс заявку? (y/n): ", end="")
    confirm = input().strip().lower()
    
    if confirm in ['y', 'yes', 'да', 'д']:
        return place_stop_loss_order(symbol, side, size, trigger_price, execute_price, order_type)
    else:
        print("❌ Размещение стоп-лосса отменено")
        return None


def place_trailing_stop():
    """Размещение трейлинг стоп-лосса"""
    print("📈 РАЗМЕЩЕНИЕ ТРЕЙЛИНГ СТОП-ЛОССА")
    print("=" * 45)
    
    symbol = input("💱 Торговая пара (по умолчанию BTCUSDT): ").strip().upper()
    if not symbol:
        symbol = "BTCUSDT"
    
    # Сторона заявки
    print("\\n🔄 Для закрытия позиции выберите ПРОТИВОПОЛОЖНУЮ сторону:")
    print("1. 🟢 Buy (для закрытия SHORT позиции)")
    print("2. 🔴 Sell (для закрытия LONG позиции)")
    
    side_input = input("Сторона (1-2): ").strip()
    if side_input == "1":
        side = "buy"
        side_display = "🟢 BUY (закрытие SHORT)"
        position_type = "SHORT"
    elif side_input == "2":
        side = "sell"
        side_display = "🔴 SELL (закрытие LONG)"
        position_type = "LONG"
    else:
        side = "sell"
        side_display = "🔴 SELL (закрытие LONG)"
        position_type = "LONG"
    
    # Размер позиции
    size_input = input(f"📊 Размер позиции для закрытия (контракты): ").strip()
    try:
        size = str(float(size_input))
    except ValueError:
        print("❌ Неверный размер")
        return None
    
    # Трейлинг расстояние
    trailing_input = input(f"📏 Трейлинг расстояние (%): ").strip()
    try:
        trailing_pct = float(trailing_input) / 100
    except ValueError:
        trailing_pct = 0.02  # 2% по умолчанию
    
    # Активация трейлинга
    activation_input = input(f"🎯 Цена активации трейлинга (опционально): ").strip()
    if activation_input:
        try:
            activation_price = str(float(activation_input))
        except ValueError:
            activation_price = None
    else:
        activation_price = None
    
    print(f"\\n❌ ВНИМАНИЕ: Трейлинг стоп-лосс не поддерживается напрямую через API")
    print(f"📋 Можно создать обычный стоп-лосс с последующим ручным управлением")
    print(f"\\n💡 Альтернативы:")
    print(f"   1. Использовать веб-интерфейс Bitget для трейлинг стопа")
    print(f"   2. Реализовать логику трейлинга через программный мониторинг")
    print(f"   3. Разместить обычный стоп-лосс и обновлять его вручную")
    
    # Предлагаем разместить обычный стоп-лосс
    current_price_input = input(f"\\n💰 Введите текущую рыночную цену для расчета стопа: ").strip()
    try:
        current_price = float(current_price_input)
        
        if position_type == "LONG":
            suggested_stop = current_price * (1 - trailing_pct)
            print(f"📉 Предлагаемый стоп-лосс: ${suggested_stop:.4f} ({trailing_pct*100:.1f}% ниже)")
        else:
            suggested_stop = current_price * (1 + trailing_pct)
            print(f"📈 Предлагаемый стоп-лосс: ${suggested_stop:.4f} ({trailing_pct*100:.1f}% выше)")
        
        confirm = input(f"🛡️ Разместить обычный стоп-лосс на ${suggested_stop:.4f}? (y/n): ").strip().lower()
        
        if confirm in ['y', 'yes', 'да', 'д']:
            return place_stop_loss_order(symbol, side, size, str(suggested_stop))
    
    except ValueError:
        print("❌ Неверная цена")
    
    return None


def manage_stop_loss_orders():
    """Управление стоп-лосс заявками"""
    print("🛡️ УПРАВЛЕНИЕ СТОП-ЛОСС ЗАЯВКАМИ")
    print("=" * 50)
    
    print("\\n📋 Доступные действия:")
    print("1. 📊 Просмотр активных стоп-лоссов")
    print("2. ✏️ Изменение стоп-лосса")
    print("3. ❌ Отмена стоп-лосса")
    print("4. 🔄 Массовое управление")
    
    choice = input("\\nВыберите действие (1-4): ").strip()
    
    if choice == "1":
        print("\\n📊 Для просмотра активных заявок используйте get_pending_orders.py")
    elif choice == "2":
        print("\\n✏️ Для изменения заявок используйте modify_order.py")
    elif choice == "3":
        print("\\n❌ Для отмены заявок используйте cancel_order.py")
    elif choice == "4":
        print("\\n🔄 Для массовых операций используйте batch_cancel_orders.py")
    else:
        print("❌ Неверный выбор")


def calculate_stop_loss_levels():
    """Калькулятор уровней стоп-лосса"""
    print("🧮 КАЛЬКУЛЯТОР СТОП-ЛОСС УРОВНЕЙ")
    print("=" * 45)
    
    # Текущая цена позиции
    entry_price_input = input("💰 Цена входа в позицию: ").strip()
    try:
        entry_price = float(entry_price_input)
    except ValueError:
        print("❌ Неверная цена входа")
        return
    
    # Тип позиции
    print("\\n📊 Тип позиции:")
    print("1. 🟢 LONG (покупка)")
    print("2. 🔴 SHORT (продажа)")
    
    position_input = input("Тип позиции (1-2): ").strip()
    is_long = position_input == "1"
    
    # Размер позиции
    position_size_input = input("📏 Размер позиции (контракты): ").strip()
    try:
        position_size = float(position_size_input)
    except ValueError:
        position_size = 1.0
    
    # Приемлемый уровень потерь
    max_loss_input = input("💸 Максимальные потери (USD): ").strip()
    try:
        max_loss = float(max_loss_input)
    except ValueError:
        max_loss = None
    
    print(f"\\n🧮 РАСЧЕТ СТОП-ЛОСС УРОВНЕЙ:")
    print("=" * 60)
    
    print(f"{'Риск %':^10} {'Цена стопа':^15} {'Потери USD':^15} {'Расстояние':^15}")
    print("-" * 60)
    
    risk_levels = [1, 2, 3, 5, 10, 15, 20]
    
    for risk_pct in risk_levels:
        if is_long:
            # Для LONG позиции стоп ниже цены входа
            stop_price = entry_price * (1 - risk_pct / 100)
            loss_per_contract = entry_price - stop_price
        else:
            # Для SHORT позиции стоп выше цены входа
            stop_price = entry_price * (1 + risk_pct / 100)
            loss_per_contract = stop_price - entry_price
        
        total_loss = loss_per_contract * position_size
        price_distance = abs(stop_price - entry_price)
        
        # Отмечаем оптимальный уровень
        marker = ""
        if max_loss and total_loss <= max_loss:
            marker = " ✅"
        elif total_loss > max_loss if max_loss else False:
            marker = " ❌"
        
        print(f"{risk_pct:>7}% ${stop_price:>13.2f} ${total_loss:>13.2f} ${price_distance:>13.2f}{marker}")
    
    print("-" * 60)
    
    # Рекомендации
    print(f"\\n💡 РЕКОМЕНДАЦИИ:")
    print(f"   🎯 Цена входа: ${entry_price:.2f}")
    print(f"   📊 Размер позиции: {position_size} контрактов")
    
    if max_loss:
        print(f"   💸 Лимит потерь: ${max_loss:.2f}")
        
        # Находим оптимальный уровень
        for risk_pct in risk_levels:
            if is_long:
                stop_price = entry_price * (1 - risk_pct / 100)
                loss_per_contract = entry_price - stop_price
            else:
                stop_price = entry_price * (1 + risk_pct / 100)
                loss_per_contract = stop_price - entry_price
            
            total_loss = loss_per_contract * position_size
            
            if total_loss <= max_loss:
                print(f"   ✅ Оптимальный стоп: ${stop_price:.2f} (риск {risk_pct}%)")
                break
    
    # Общие рекомендации по риск-менеджменту
    print(f"\\n🛡️ ПРАВИЛА РИСК-МЕНЕДЖМЕНТА:")
    print(f"   📈 Новички: 1-2% риска на сделку")
    print(f"   📊 Опытные: 2-5% риска на сделку")
    print(f"   🔥 Максимум: не более 10% на сделку")
    print(f"   💰 Общий риск портфеля: не более 20%")


def main():
    """Основная функция"""
    print("🛡️ BITGET FUTURES - СТОП-ЛОСС ЗАЯВКИ")
    print("=" * 50)
    
    print("\\n🔌 Выберите режим:")
    print("1. 🛡️ Разместить стоп-лосс")
    print("2. 🔍 Интерактивное размещение")
    print("3. 📈 Трейлинг стоп-лосс")
    print("4. 🛠️ Управление стоп-лоссами")
    print("5. 🧮 Калькулятор уровней")
    
    try:
        choice = input("\\nВаш выбор (1-5): ").strip()
        
        if choice == "1":
            # Пример стоп-лосса
            place_stop_loss_order("BTCUSDT", "sell", "0.01", "35000")
        elif choice == "2":
            place_stop_loss_interactive()
        elif choice == "3":
            place_trailing_stop()
        elif choice == "4":
            manage_stop_loss_orders()
        elif choice == "5":
            calculate_stop_loss_levels()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
