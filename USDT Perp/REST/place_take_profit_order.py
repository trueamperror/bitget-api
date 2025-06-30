#!/usr/bin/env python3
"""
Bitget USDT Perpetual REST API - Place Take Profit Order

Размещение тейк-профит ордера для фьючерсов.
Автоматическое закрытие позиции при достижении целевой прибыли.

Документация: https://www.bitget.com/api-doc/contract/trade/Place-Order

Параметры:
- symbol: торговая пара (обязательный)
- side: сторона (противоположная открытой позиции)
- size: размер позиции для закрытия
- triggerPrice: цена срабатывания тейк-профита
- orderType: take_profit
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


def place_take_profit_order(symbol, side, size, trigger_price, client_oid=None):
    """
    Размещение тейк-профит ордера
    
    Args:
        symbol (str): Торговая пара (например, BTCUSDT)
        side (str): Сторона закрытия (buy для шорта, sell для лонга)
        size (str): Размер позиции для закрытия
        trigger_price (str): Цена срабатывания тейк-профита
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
    request_path = '/api/v2/mix/order/place-plan-order'
    
    # Генерируем клиентский ID если не предоставлен
    if not client_oid:
        client_oid = f"take_profit_{int(time.time())}"
    
    body_data = {
        'symbol': symbol,
        'productType': 'USDT-FUTURES',
        'marginMode': 'crossed',
        'marginCoin': 'USDT',
        'side': side,
        'orderType': 'market',
        'size': str(size),
        'triggerPrice': str(trigger_price),
        'triggerType': 'mark_price',
        'planType': 'normal_plan',  # Используем normal_plan 
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
        position_type = "ШОРТ" if side == "buy" else "ЛОНГ"
        
        print(f"🎯 Размещение тейк-профит ордера...")
        print(f"💱 Пара: {symbol}")
        print(f"{side_emoji} Закрытие {position_type} позиции")
        print(f"📊 Размер: {size}")
        print(f"🎯 Цена тейк-профита: ${trigger_price}")
        print(f"🆔 Client OID: {client_oid}")
        
        response = requests.post(url, headers=headers, data=body)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == '00000':
                order_data = data.get('data', {})
                
                print("\\n✅ Тейк-профит ордер успешно размещен!")
                print("=" * 50)
                
                # Информация об ордере
                order_id = order_data.get('orderId', 'N/A')
                client_order_id = order_data.get('clientOid', client_oid)
                
                print(f"🆔 ID ордера: {order_id}")
                print(f"👤 Client OID: {client_order_id}")
                print(f"💱 Символ: {symbol}")
                print(f"{side_emoji} Сторона: {side.upper()}")
                print(f"📊 Размер: {size}")
                print(f"🎯 Тип: TAKE PROFIT")
                print(f"💰 Цена срабатывания: ${trigger_price}")
                
                # Детальное объяснение механизма
                print(f"\\n💡 МЕХАНИЗМ ТЕЙК-ПРОФИТА:")
                if side == "sell":  # Закрытие лонг позиции
                    print("📈 Закрытие ЛОНГ позиции:")
                    print(f"• При росте цены до ${trigger_price}")
                    print("• Автоматическая продажа по рыночной цене")
                    print("• Фиксация прибыли от роста")
                else:  # Закрытие шорт позиции
                    print("📉 Закрытие ШОРТ позиции:")
                    print(f"• При падении цены до ${trigger_price}")
                    print("• Автоматическая покупка по рыночной цене")
                    print("• Фиксация прибыли от падения")
                
                # Расчет потенциальной прибыли (приблизительный)
                try:
                    size_float = float(size)
                    trigger_float = float(trigger_price)
                    notional = size_float * trigger_float
                    
                    print(f"\\n📊 РАСЧЕТЫ:")
                    print(f"💰 Стоимость закрытия: ${notional:,.2f}")
                    
                    if notional > 10000:
                        print(f"🎯 КРУПНАЯ ПОЗИЦИЯ: ${notional:,.2f}")
                        print("✅ Хорошая стратегия фиксации прибыли!")
                    
                except:
                    pass
                
                print(f"\\n✅ ПРЕИМУЩЕСТВА ТЕЙК-ПРОФИТА:")
                print("• 🎯 Автоматическая фиксация прибыли")
                print("• 😴 Работает без постоянного мониторинга")
                print("• 💰 Защита от разворота тренда")
                print("• 📊 Дисциплинированная торговля")
                
                print(f"\\n⚠️ ВАЖНЫЕ ЗАМЕЧАНИЯ:")
                print("• 🔄 Исполнение по рыночной цене")
                print("• 📈 Возможное проскальзывание")
                print("• ⏰ Мгновенное срабатывание при достижении цены")
                print("• 💡 Рекомендуется комбинировать со стоп-лоссом")
                
                return data
            else:
                print(f"❌ Ошибка API: {data.get('msg', 'Unknown error')}")
                
                # Детальная обработка ошибок
                error_msg = data.get('msg', '').lower()
                if 'insufficient' in error_msg:
                    print("💡 Проверьте наличие открытой позиции")
                elif 'price' in error_msg:
                    print("💡 Проверьте корректность цены тейк-профита")
                elif 'size' in error_msg:
                    print("💡 Размер не должен превышать размер позиции")
                
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


def get_current_positions(symbol=None):
    """Получение текущих позиций для анализа"""
    config = load_config()
    if not config:
        return None
    
    timestamp = str(int(time.time() * 1000))
    method = 'GET'
    request_path = '/api/v2/mix/position/all-position'
    query_string = 'productType=USDT-FUTURES'
    
    if symbol:
        query_string += f'&symbol={symbol}'
    
    signature = generate_signature(timestamp, method, request_path, query_string)
    if not signature:
        return None
    
    headers = {
        'ACCESS-KEY': config['apiKey'],
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': config['passphrase'],
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }
    
    try:
        url = f"{config['baseURL']}{request_path}?{query_string}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '00000':
                return data.get('data', [])
        
        return []
    except:
        return []


def place_take_profit_interactive():
    """Интерактивное размещение тейк-профит ордера"""
    print("🎯 РАЗМЕЩЕНИЕ ТЕЙК-ПРОФИТ ОРДЕРА")
    print("=" * 40)
    
    # Получаем символ
    symbol = input("💱 Введите торговую пару (например, BTCUSDT): ").strip().upper()
    if not symbol:
        print("❌ Торговая пара не указана")
        return None
    
    # Проверяем текущие позиции
    print(f"\\n🔍 Проверка текущих позиций для {symbol}...")
    positions = get_current_positions(symbol)
    
    current_position = None
    if positions:
        for pos in positions:
            if pos.get('symbol') == symbol:
                size = float(pos.get('size', 0))
                if size != 0:
                    current_position = pos
                    break
    
    if current_position:
        pos_side = current_position.get('side', 'unknown')
        pos_size = current_position.get('size', '0')
        pos_price = current_position.get('averageOpenPrice', '0')
        unrealized_pnl = current_position.get('unrealizedPL', '0')
        
        side_emoji = "🟢" if pos_side == "long" else "🔴"
        pnl_emoji = "📈" if float(unrealized_pnl) > 0 else "📉"
        
        print(f"✅ Найдена открытая позиция:")
        print(f"{side_emoji} Направление: {pos_side.upper()}")
        print(f"📊 Размер: {pos_size}")
        print(f"💰 Средняя цена: ${pos_price}")
        print(f"{pnl_emoji} Нереализованный PnL: ${unrealized_pnl}")
        
        # Автоматически определяем сторону закрытия
        close_side = "sell" if pos_side == "long" else "buy"
        
        use_current = input(f"\\nИспользовать текущую позицию? (yes/no): ").strip().lower()
        if use_current in ['yes', 'y', 'да']:
            side = close_side
            size = pos_size
            
            print(f"\\n✅ Настройка для закрытия {pos_side.upper()} позиции:")
            print(f"📊 Размер: {size}")
            print(f"🔄 Сторона закрытия: {side.upper()}")
        else:
            # Ручной ввод параметров
            side = None
            size = None
    else:
        print("ℹ️ Открытых позиций не найдено")
        side = None
        size = None
    
    # Получаем параметры если не определены автоматически
    if not side:
        print("\\n📊 Какую позицию закрываете?")
        print("1. 🟢 Закрыть ЛОНГ (продать)")
        print("2. 🔴 Закрыть ШОРТ (купить)")
        
        side_choice = input("Ваш выбор (1-2): ").strip()
        
        if side_choice == "1":
            side = "sell"
            print("🟢 Тейк-профит для ЛОНГ позиции (продажа)")
        elif side_choice == "2":
            side = "buy"
            print("🔴 Тейк-профит для ШОРТ позиции (покупка)")
        else:
            print("❌ Неверный выбор")
            return None
    
    if not size:
        try:
            size = input(f"📊 Введите размер для закрытия: ").strip()
            size_float = float(size)
            if size_float <= 0:
                print("❌ Размер должен быть больше 0")
                return None
        except ValueError:
            print("❌ Неверный размер")
            return None
    
    # Получаем цену тейк-профита
    try:
        print(f"\\n💡 Рекомендации по цене тейк-профита:")
        if side == "sell":  # Закрытие лонга
            print("📈 Для ЛОНГ: цена должна быть ВЫШЕ цены входа")
            print("🎯 Обычно +2-5% от цены входа")
        else:  # Закрытие шорта
            print("📉 Для ШОРТ: цена должна быть НИЖЕ цены входа")
            print("🎯 Обычно -2-5% от цены входа")
        
        trigger_price = input(f"💰 Введите цену тейк-профита ($): ").strip()
        trigger_float = float(trigger_price)
        if trigger_float <= 0:
            print("❌ Цена тейк-профита должна быть больше 0")
            return None
    except ValueError:
        print("❌ Неверная цена тейк-профита")
        return None
    
    # Клиентский ID (опционально)
    client_oid = input("🆔 Client OID (необязательно): ").strip()
    if not client_oid:
        client_oid = None
    
    # Показываем сводку
    print(f"\\n📋 ПОДТВЕРЖДЕНИЕ ТЕЙК-ПРОФИТ ОРДЕРА:")
    print("=" * 45)
    side_emoji = "🟢" if side == "sell" else "🔴"
    position_type = "ЛОНГ" if side == "sell" else "ШОРТ"
    
    print(f"💱 Пара: {symbol}")
    print(f"{side_emoji} Закрытие {position_type} позиции")
    print(f"📊 Размер: {size}")
    print(f"🎯 Цена тейк-профита: ${trigger_price}")
    
    # Расчет потенциальной прибыли
    if current_position and current_position.get('averageOpenPrice'):
        try:
            entry_price = float(current_position.get('averageOpenPrice', 0))
            size_float = float(size)
            
            if side == "sell":  # Лонг позиция
                profit_per_unit = trigger_float - entry_price
                profit_pct = (profit_per_unit / entry_price) * 100
            else:  # Шорт позиция
                profit_per_unit = entry_price - trigger_float
                profit_pct = (profit_per_unit / entry_price) * 100
            
            total_profit = profit_per_unit * size_float
            
            print(f"\\n💰 РАСЧЕТ ПРИБЫЛИ:")
            print(f"📈 Цена входа: ${entry_price:.4f}")
            print(f"🎯 Цена выхода: ${trigger_float:.4f}")
            print(f"💵 Прибыль за единицу: ${profit_per_unit:.4f}")
            print(f"📊 Прибыль в %: {profit_pct:.2f}%")
            print(f"💰 Общая прибыль: ${total_profit:.2f}")
            
            if profit_pct < 1:
                print("⚠️ Низкая прибыльность (< 1%)")
            elif profit_pct > 10:
                print("🎯 Высокая прибыльность (> 10%)")
            
        except:
            pass
    
    # Логика исполнения
    print(f"\\n💡 ЛОГИКА ИСПОЛНЕНИЯ:")
    if side == "sell":
        print(f"📈 При росте цены до ${trigger_price} → автоматическая продажа")
    else:
        print(f"📉 При падении цены до ${trigger_price} → автоматическая покупка")
    print("🔄 Исполнение по рыночной цене")
    
    confirm = input("\\nПодтвердить размещение тейк-профита? (yes/no): ").strip().lower()
    
    if confirm in ['yes', 'y', 'да']:
        return place_take_profit_order(symbol, side, size, trigger_price, client_oid)
    else:
        print("❌ Размещение отменено")
        return None


def place_profit_ladder():
    """Размещение лестницы тейк-профитов"""
    print("📈 ЛЕСТНИЦА ТЕЙК-ПРОФИТОВ")
    print("=" * 40)
    print("💡 Постепенная фиксация прибыли на разных уровнях")
    
    symbol = input("💱 Торговая пара: ").strip().upper()
    if not symbol:
        print("❌ Торговая пара не указана")
        return None
    
    # Проверяем позицию
    positions = get_current_positions(symbol)
    current_position = None
    
    if positions:
        for pos in positions:
            if pos.get('symbol') == symbol and float(pos.get('size', 0)) != 0:
                current_position = pos
                break
    
    if not current_position:
        print("❌ Открытая позиция не найдена")
        return None
    
    pos_side = current_position.get('side', 'unknown')
    pos_size = float(current_position.get('size', 0))
    pos_price = float(current_position.get('averageOpenPrice', 0))
    
    side_emoji = "🟢" if pos_side == "long" else "🔴"
    close_side = "sell" if pos_side == "long" else "buy"
    
    print(f"\\n✅ Позиция найдена:")
    print(f"{side_emoji} {pos_side.upper()} {pos_size} по цене ${pos_price:.4f}")
    
    try:
        levels = int(input("📊 Количество уровней тейк-профита (2-5): ").strip())
        if levels < 2 or levels > 5:
            print("❌ Количество уровней должно быть от 2 до 5")
            return None
        
        print(f"\\n💰 Введите {levels} цен тейк-профита:")
        prices = []
        sizes = []
        
        remaining_size = pos_size
        
        for i in range(levels):
            price = float(input(f"🎯 Уровень {i+1} - цена: ").strip())
            
            if i < levels - 1:
                size_pct = float(input(f"📊 Уровень {i+1} - % позиции (от оставшегося): ").strip())
                size = (remaining_size * size_pct) / 100
                remaining_size -= size
            else:
                size = remaining_size  # Остаток на последний уровень
            
            prices.append(price)
            sizes.append(size)
            
            print(f"✅ Уровень {i+1}: ${price:.4f} | Размер: {size:.4f}")
        
        print(f"\\n📋 ЛЕСТНИЦА ТЕЙК-ПРОФИТОВ:")
        print("=" * 50)
        
        total_profit = 0
        for i, (price, size) in enumerate(zip(prices, sizes), 1):
            if pos_side == "long":
                profit = (price - pos_price) * size
            else:
                profit = (pos_price - price) * size
            
            total_profit += profit
            print(f"🎯 Уровень {i}: ${price:.4f} | {size:.4f} | Прибыль: ${profit:.2f}")
        
        print(f"💰 Общая потенциальная прибыль: ${total_profit:.2f}")
        
        confirm = input("\\nРазместить лестницу тейк-профитов? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y', 'да']:
            success_count = 0
            
            for i, (price, size) in enumerate(zip(prices, sizes), 1):
                print(f"\\n[{i}/{levels}] Размещение уровня {i}...")
                client_oid = f"tp_ladder_{i}_{int(time.time())}"
                
                result = place_take_profit_order(symbol, close_side, str(size), str(price), client_oid)
                if result:
                    success_count += 1
                    print(f"✅ Уровень {i} размещен")
                else:
                    print(f"❌ Ошибка размещения уровня {i}")
                
                # Пауза между запросами
                time.sleep(0.5)
            
            print(f"\\n📊 РЕЗУЛЬТАТ:")
            print(f"✅ Успешно размещено: {success_count}/{levels}")
            print(f"❌ Ошибок: {levels - success_count}/{levels}")
            
            return success_count > 0
        else:
            print("❌ Размещение отменено")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None


def main():
    """Основная функция"""
    print("🎯 BITGET USDT PERP - ТЕЙК-ПРОФИТ ОРДЕРА")
    print("=" * 50)
    
    print("\\n🔌 Выберите режим:")
    print("1. 🎯 Тейк-профит ордер")
    print("2. 🔍 Интерактивное размещение")
    print("3. 📈 Лестница тейк-профитов")
    print("4. 📊 Проверить позиции")
    
    try:
        choice = input("\\nВаш выбор (1-4): ").strip()
        
        if choice == "1":
            symbol = input("💱 Торговая пара: ").strip().upper()
            side = input("📊 Сторона (buy/sell): ").strip().lower()
            size = input("📊 Размер: ").strip()
            trigger_price = input("🎯 Цена тейк-профита: ").strip()
            
            if all([symbol, side, size, trigger_price]):
                place_take_profit_order(symbol, side, size, trigger_price)
            else:
                print("❌ Не все параметры указаны")
                
        elif choice == "2":
            place_take_profit_interactive()
            
        elif choice == "3":
            place_profit_ladder()
            
        elif choice == "4":
            symbol = input("💱 Торговая пара (или Enter для всех): ").strip().upper()
            positions = get_current_positions(symbol if symbol else None)
            
            if positions:
                print(f"\\n📊 ОТКРЫТЫЕ ПОЗИЦИИ:")
                print("=" * 60)
                
                for pos in positions:
                    if float(pos.get('size', 0)) != 0:
                        symbol = pos.get('symbol', 'N/A')
                        side = pos.get('side', 'unknown')
                        size = pos.get('size', '0')
                        price = pos.get('averageOpenPrice', '0')
                        pnl = pos.get('unrealizedPL', '0')
                        
                        side_emoji = "🟢" if side == "long" else "🔴"
                        pnl_emoji = "📈" if float(pnl) > 0 else "📉"
                        
                        print(f"{side_emoji} {symbol} | {side.upper()} | {size} | ${price} | {pnl_emoji} ${pnl}")
            else:
                print("ℹ️ Открытых позиций не найдено")
                
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
