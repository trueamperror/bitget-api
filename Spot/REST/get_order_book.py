# -*- coding: utf-8 -*-
"""
Bitget Spot REST API - Get Order Book
Получение книги ордеров (стакан заявок)

Документация: https://www.bitget.com/api-doc/spot/market/Get-Orderbook

Описание:
Этот скрипт получает книгу ордеров (стакан заявок) для указанной торговой пары
на спот рынке Bitget. Показывает лучшие цены покупки и продажи.

Параметры:
- symbol: торговая пара (обязательно, например BTCUSDT)
- type: тип стакана (step0, step1, step2, step3, step4, step5)
- limit: количество уровней (по умолчанию 100, максимум 500)

Типы стакана:
- step0: без группировки
- step1-step5: различные уровни группировки цен

Возвращаемые данные:
- asks: заявки на продажу [[цена, количество], ...]
- bids: заявки на покупку [[цена, количество], ...]
- ts: временная метка
"""

import requests
import json
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
BASE_URL = config.get('baseURL', 'https://api.bitget.com')

def get_order_book(symbol, type_step="step0", limit=100):
    """
    Получение книги ордеров
    
    Args:
        symbol (str): Торговая пара (например, BTCUSDT)
        type_step (str): Тип группировки (step0-step5)
        limit (int): Количество уровней (максимум 500)
    
    Returns:
        dict: Данные книги ордеров или None при ошибке
    """
    
    # Формируем URL эндпоинта
    endpoint = f"{BASE_URL}/api/v2/spot/market/orderbook"
    
    # Параметры запроса
    params = {
        'symbol': symbol,
        'type': type_step,
        'limit': str(limit)
    }
    
    try:
        print(f"📚 Запрос книги ордеров...")
        print(f"💱 Пара: {symbol}")
        print(f"📊 Тип: {type_step}, Лимит: {limit}")
        
        # Выполняем запрос (публичный эндпоинт, не требует аутентификации)
        response = requests.get(endpoint, params=params, timeout=10)
        
        # Проверяем статус ответа
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем код ответа Bitget
            if data.get('code') == '00000':
                order_book_data = data.get('data')
                if order_book_data:
                    print(f"✅ Книга ордеров получена")
                    return order_book_data
                else:
                    print("⚠️ Данные книги ордеров не найдены")
                    return None
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

def format_order_book_response(order_book_data, symbol):
    """
    Форматирование ответа с книгой ордеров
    
    Args:
        order_book_data (dict): Данные книги ордеров
        symbol (str): Торговая пара
    """
    
    if not order_book_data:
        print("📊 Нет данных для отображения")
        return
    
    asks = order_book_data.get('asks', [])
    bids = order_book_data.get('bids', [])
    timestamp = order_book_data.get('ts', 0)
    
    # Форматируем время
    if timestamp:
        time_str = datetime.fromtimestamp(int(timestamp) / 1000).strftime('%Y-%m-%d %H:%M:%S')
    else:
        time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"\\n📚 КНИГА ОРДЕРОВ - {symbol}")
    print("=" * 80)
    print(f"⏰ Время: {time_str}")
    print(f"📊 Заявки на продажу: {len(asks)}")
    print(f"📊 Заявки на покупку: {len(bids)}")
    
    # Показываем только топ уровни для читаемости
    max_levels = 10
    
    print(f"\\n📊 ТОП {max_levels} УРОВНЕЙ КНИГИ ОРДЕРОВ")
    print("=" * 80)
    print(f"{'ASKS (Продажа)':^35} | {'BIDS (Покупка)':^35}")
    print(f"{'Цена':>15} {'Количество':>15} | {'Цена':>15} {'Количество':>15}")
    print("-" * 80)
    
    # Конвертируем в числа и сортируем
    try:
        # Обрабатываем asks (сортируем по возрастанию цены)
        asks_processed = []
        for ask in asks[:max_levels]:
            if len(ask) >= 2:
                price = float(ask[0])
                quantity = float(ask[1])
                asks_processed.append((price, quantity))
        
        asks_processed.sort(key=lambda x: x[0])
        
        # Обрабатываем bids (сортируем по убыванию цены)
        bids_processed = []
        for bid in bids[:max_levels]:
            if len(bid) >= 2:
                price = float(bid[0])
                quantity = float(bid[1])
                bids_processed.append((price, quantity))
        
        bids_processed.sort(key=lambda x: x[0], reverse=True)
        
        # Выводим уровни
        max_rows = max(len(asks_processed), len(bids_processed))
        
        for i in range(max_rows):
            ask_price = f"{asks_processed[i][0]:,.8f}" if i < len(asks_processed) else ""
            ask_qty = f"{asks_processed[i][1]:,.6f}" if i < len(asks_processed) else ""
            bid_price = f"{bids_processed[i][0]:,.8f}" if i < len(bids_processed) else ""
            bid_qty = f"{bids_processed[i][1]:,.6f}" if i < len(bids_processed) else ""
            
            print(f"{ask_price:>15} {ask_qty:>15} | {bid_price:>15} {bid_qty:>15}")
        
        # Расчет статистики
        if asks_processed and bids_processed:
            best_ask = asks_processed[0][0]  # Минимальная цена продажи
            best_bid = bids_processed[0][0]  # Максимальная цена покупки
            
            spread = best_ask - best_bid
            spread_percent = (spread / best_ask) * 100
            mid_price = (best_ask + best_bid) / 2
            
            print(f"\\n💰 СТАТИСТИКА СПРЕДА:")
            print("-" * 40)
            print(f"🟢 Лучший бид (покупка): {best_bid:,.8f}")
            print(f"🔴 Лучший аск (продажа): {best_ask:,.8f}")
            print(f"📊 Спред: {spread:,.8f} ({spread_percent:.4f}%)")
            print(f"📊 Средняя цена: {mid_price:,.8f}")
        
        # Анализ глубины
        if asks_processed and bids_processed:
            # Объемы на разных уровнях
            ask_volumes = [qty for _, qty in asks_processed]
            bid_volumes = [qty for _, qty in bids_processed]
            
            total_ask_volume = sum(ask_volumes)
            total_bid_volume = sum(bid_volumes)
            
            print(f"\\n📦 АНАЛИЗ ОБЪЕМОВ (топ {len(asks_processed)} уровней):")
            print("-" * 50)
            print(f"🔴 Общий объем asks: {total_ask_volume:,.6f}")
            print(f"🟢 Общий объем bids: {total_bid_volume:,.6f}")
            print(f"📊 Соотношение bid/ask: {total_bid_volume/total_ask_volume:.4f}" if total_ask_volume > 0 else "📊 Соотношение bid/ask: N/A")
            
            # Средние объемы
            avg_ask_volume = total_ask_volume / len(ask_volumes) if ask_volumes else 0
            avg_bid_volume = total_bid_volume / len(bid_volumes) if bid_volumes else 0
            
            print(f"📊 Средний объем ask: {avg_ask_volume:,.6f}")
            print(f"📊 Средний объем bid: {avg_bid_volume:,.6f}")
            
            # Анализ концентрации ликвидности
            if len(asks_processed) >= 3 and len(bids_processed) >= 3:
                top3_ask_volume = sum(ask_volumes[:3])
                top3_bid_volume = sum(bid_volumes[:3])
                
                ask_concentration = (top3_ask_volume / total_ask_volume) * 100 if total_ask_volume > 0 else 0
                bid_concentration = (top3_bid_volume / total_bid_volume) * 100 if total_bid_volume > 0 else 0
                
                print(f"\\n🎯 КОНЦЕНТРАЦИЯ ЛИКВИДНОСТИ (топ 3 уровня):")
                print("-" * 50)
                print(f"🔴 Концентрация asks: {ask_concentration:.1f}%")
                print(f"🟢 Концентрация bids: {bid_concentration:.1f}%")
        
    except (ValueError, IndexError) as e:
        print(f"❌ Ошибка обработки данных: {e}")

def analyze_market_depth(order_book_data, price_levels=[0.1, 0.5, 1.0, 2.0]):
    """
    Анализ глубины рынка на разных уровнях от лучшей цены
    
    Args:
        order_book_data (dict): Данные книги ордеров
        price_levels (list): Уровни отклонения цены в процентах
    """
    
    asks = order_book_data.get('asks', [])
    bids = order_book_data.get('bids', [])
    
    if not asks or not bids:
        return
    
    try:
        best_ask = float(asks[0][0])
        best_bid = float(bids[0][0])
        
        print(f"\\n📊 АНАЛИЗ ГЛУБИНЫ РЫНКА:")
        print("-" * 60)
        print(f"{'Уровень %':^10} {'Ask Volume':^15} {'Bid Volume':^15} {'Дисбаланс':^15}")
        print("-" * 60)
        
        for level_percent in price_levels:
            ask_threshold = best_ask * (1 + level_percent / 100)
            bid_threshold = best_bid * (1 - level_percent / 100)
            
            # Подсчет объема до указанного уровня
            ask_volume = sum(float(ask[1]) for ask in asks if float(ask[0]) <= ask_threshold)
            bid_volume = sum(float(bid[1]) for bid in bids if float(bid[0]) >= bid_threshold)
            
            # Дисбаланс (положительный = больше покупателей)
            imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume) * 100 if (bid_volume + ask_volume) > 0 else 0
            
            print(f"{level_percent:^10.1f}% {ask_volume:^15.2f} {bid_volume:^15.2f} {imbalance:^15.1f}%")
            
    except (ValueError, IndexError) as e:
        print(f"❌ Ошибка анализа глубины: {e}")

def main():
    """Основная функция"""
    print("📚 Bitget Spot REST API - Get Order Book")
    print("=" * 55)
    
    # Параметры по умолчанию
    symbol = "BTCUSDT"
    type_step = "step0"
    limit = 50
    
    print(f"💱 Торговая пара: {symbol}")
    print(f"📊 Тип группировки: {type_step}")
    print(f"🔢 Лимит уровней: {limit}")
    
    # Получаем книгу ордеров
    order_book = get_order_book(symbol, type_step, limit)
    
    # Выводим сырой JSON ответ
    if order_book:
        import json
        print("\n📄 RAW JSON RESPONSE:")
        print(json.dumps(order_book, indent=2, ensure_ascii=False))
        
        # Форматируем и выводим результат
        format_order_book_response(order_book, symbol)
        analyze_market_depth(order_book)
        
        # Демонстрация разных типов группировки
        print(f"\\n🔍 ДЕМОНСТРАЦИЯ РАЗНЫХ ТИПОВ ГРУППИРОВКИ:")
        print("-" * 50)
        
        for step_type in ["step1", "step2"]:
            print(f"\\n📊 Тип группировки: {step_type}")
            step_order_book = get_order_book(symbol, step_type, 5)
            if step_order_book:
                asks = step_order_book.get('asks', [])
                bids = step_order_book.get('bids', [])
                print(f"   🔴 Топ ask: {asks[0][0]} (qty: {asks[0][1]})" if asks else "   🔴 Нет asks")
                print(f"   🟢 Топ bid: {bids[0][0]} (qty: {bids[0][1]})" if bids else "   🟢 Нет bids")
    else:
        print("❌ Не удалось получить книгу ордеров")

if __name__ == "__main__":
    main()
