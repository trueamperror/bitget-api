#!/usr/bin/env python3
"""
Bitget API - Получение информации о торговых парах (USDT Perpetual Futures)
Получение списка всех доступных фьючерсных контрактов и их параметров

Официальная документация:
https://www.bitget.com/api-doc/contract/market/Get-Symbol-Information

Требует аутентификации: Нет
Лимит запросов: 20 запросов/секунду
"""

import requests
import json
from datetime import datetime

def get_symbol_info():
    """Получение информации о торговых парах"""
    
    url = "https://api.bitget.com/api/v2/mix/market/contracts"
    
    # Параметры запроса для USDT Perpetual
    params = {
        'productType': 'USDT-FUTURES'  # USDT Perpetual Futures
    }
    
    try:
        print("🚀 Bitget USDT Perpetual Futures - Get Symbol Info")
        print("=" * 60)
        print("🔍 Запрос информации о торговых парах...")
        print(f"🌐 Эндпоинт: {url}")
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Запрос выполнен успешно")
            print("📋 RAW JSON Response от биржи (первые 3 символа):")
            print("=" * 50)
            
            # Показываем только первые 3 символа для экономии места
            display_data = data.copy()
            if display_data.get('data') and len(display_data['data']) > 3:
                display_data['data'] = display_data['data'][:3]
                print(json.dumps(display_data, indent=2, ensure_ascii=False))
                print(f"... (показаны первые 3 из {len(data.get('data', []))} символов)")
            else:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            print("=" * 50)
            
            return data
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def display_symbols_analysis(symbols):
    """Отображение анализа торговых пар"""
    
    print(f"\n📊 АНАЛИЗ ТОРГОВЫХ ПАР USDT PERPETUAL FUTURES")
    print("=" * 70)
    
    # Подсчет статистики
    active_symbols = [s for s in symbols if s.get('status') == 'normal']
    suspended_symbols = [s for s in symbols if s.get('status') != 'normal']
    
    print(f"🔢 Всего торговых пар: {len(symbols)}")
    print(f"🟢 Активных пар: {len(active_symbols)}")
    print(f"🔴 Неактивных/приостановленных пар: {len(suspended_symbols)}")
    
    # Топ-10 по объему
    print(f"\n📈 ТОП-10 ПАР ПО ПАРАМЕТРАМ:")
    print("-" * 100)
    print(f"{'Символ':<20} {'Статус':<10} {'Мин.размер':<15} {'Макс.размер':<15} {'Цена тика':<12} {'Плечо':<10}")
    print("-" * 100)
    
    # Сортируем по активности и выводим первые 10
    active_sorted = sorted(active_symbols, key=lambda x: x.get('symbol', ''))[:10]
    
    for symbol in active_sorted:
        symbol_name = symbol.get('symbol', 'N/A')
        status = "🟢active" if symbol.get('status') == 'normal' else "🔴inactive"
        min_size = symbol.get('minTradeNum', 'N/A')
        max_size = symbol.get('maxTradeNum', 'N/A')
        tick_size = symbol.get('priceEndStep', 'N/A')
        leverage = symbol.get('maxLever', 'N/A')
        
        print(f"{symbol_name:<20} {status:<10} {str(min_size):<15} {str(max_size):<15} {str(tick_size):<12} {str(leverage):<10}")
    
    # Статистика по базовым активам
    base_coins = {}
    for symbol in symbols:
        base_coin = symbol.get('baseCoin', 'Unknown')
        if base_coin not in base_coins:
            base_coins[base_coin] = 0
        base_coins[base_coin] += 1
    
    print(f"\n💰 СТАТИСТИКА ПО БАЗОВЫМ АКТИВАМ:")
    print("-" * 40)
    
    # Топ-10 базовых активов
    sorted_bases = sorted(base_coins.items(), key=lambda x: x[1], reverse=True)[:10]
    for base, count in sorted_bases:
        print(f"   {base}: {count} пар")

def search_symbol(symbols, search_term):
    """Поиск конкретного символа"""
    if not symbols:
        return None
    
    search_term = search_term.upper()
    found = []
    
    for symbol in symbols:
        symbol_name = symbol.get('symbol', '')
        if search_term in symbol_name:
            found.append(symbol)
    
    return found

def main():
    """Основная функция"""
    
    # Получение данных
    symbols = get_symbol_info()
    
    if not symbols:
        return
    
    # Интерактивный поиск
    while True:
        print(f"\n🔍 ПОИСК ТОРГОВЫХ ПАР")
        print("-" * 30)
        search_term = input("Введите символ для поиска (или 'exit' для выхода): ").strip()
        
        if search_term.lower() == 'exit':
            break
        
        if not search_term:
            continue
        
        found_symbols = search_symbol(symbols, search_term)
        
        if found_symbols:
            print(f"\n📊 Найдено {len(found_symbols)} совпадений:")
            print("-" * 80)
            print(f"{'Символ':<20} {'Статус':<10} {'Базовая':<10} {'Котир.':<10} {'Плечо':<10}")
            print("-" * 80)
            
            for symbol in found_symbols[:10]:  # Показываем максимум 10
                symbol_name = symbol.get('symbol', 'N/A')
                status = "🟢normal" if symbol.get('status') == 'normal' else "🔴other"
                base_coin = symbol.get('baseCoin', 'N/A')
                quote_coin = symbol.get('quoteCoin', 'N/A')
                max_lever = symbol.get('maxLever', 'N/A')
                
                print(f"{symbol_name:<20} {status:<10} {base_coin:<10} {quote_coin:<10} {str(max_lever):<10}")
                
            # Подробная информация о первом найденном
            if found_symbols:
                first_symbol = found_symbols[0]
                print(f"\n📋 Подробная информация о {first_symbol.get('symbol')}:")
                print("-" * 50)
                
                details = [
                    ('Символ', first_symbol.get('symbol')),
                    ('Статус', first_symbol.get('status')),
                    ('Базовая валюта', first_symbol.get('baseCoin')),
                    ('Котируемая валюта', first_symbol.get('quoteCoin')),
                    ('Минимальный размер', first_symbol.get('minTradeNum')),
                    ('Максимальный размер', first_symbol.get('maxTradeNum')),
                    ('Шаг цены', first_symbol.get('priceEndStep')),
                    ('Шаг размера', first_symbol.get('volumePlace')),
                    ('Максимальное плечо', first_symbol.get('maxLever')),
                    ('Минимальное плечо', first_symbol.get('minLever')),
                    ('Поддерживается ли', first_symbol.get('supportMarginMode')),
                    ('Открытие лонгов', first_symbol.get('openCostUpRate')),
                    ('Открытие шортов', first_symbol.get('openCostDownRate'))
                ]
                
                for label, value in details:
                    print(f"   {label}: {value}")
        else:
            print(f"❌ Символы с '{search_term}' не найдены")

if __name__ == "__main__":
    main()
