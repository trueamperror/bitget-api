# -*- coding: utf-8 -*-
"""
Bitget Spot REST API - Get Symbol Info
Получение информации о торговых парах

Документация: https://www.bitget.com/api-doc/spot/market/Get-Symbol-List

Описание:
Этот скрипт получает список всех доступных торговых пар (символов) на спот рынке Bitget.
Включает информацию о минимальных/максимальных размерах ордеров, точности цены и количества.

Параметры:
Этот эндпоинт не требует параметров - возвращает все доступные пары.

Возвращаемые данные:
- symbol: Название торговой пары (например, BTCUSDT)
- baseCoin: Базовая валюта (например, BTC)
- quoteCoin: Котируемая валюта (например, USDT)
- minTradeAmount: Минимальный размер ордера
- maxTradeAmount: Максимальный размер ордера
- takerFeeRate: Комиссия тейкера
- makerFeeRate: Комиссия мейкера
- priceScale: Точность цены
- quantityScale: Точность количества
- status: Статус пары (online/offline)
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

def get_symbol_info():
    """
    Получение информации о торговых парах
    
    Returns:
        list: Список торговых пар или None при ошибке
    """
    
    # Формируем URL эндпоинта
    endpoint = f"{BASE_URL}/api/v2/spot/public/symbols"
    
    try:
        print(f"🔍 Запрос информации о торговых парах...")
        print(f"🌐 Эндпоинт: {endpoint}")
        
        # Выполняем запрос (публичный эндпоинт, не требует аутентификации)
        response = requests.get(endpoint, timeout=10)
        
        # Проверяем статус ответа
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем код ответа Bitget
            if data.get('code') == '00000':
                symbols_data = data.get('data', [])
                if symbols_data:
                    print(f"✅ Получено {len(symbols_data)} торговых пар")
                    return symbols_data
                else:
                    print("⚠️ Данные о торговых парах не найдены")
                    return []
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

def format_symbol_info_response(symbols_data):
    """
    Форматирование ответа с информацией о торговых парах
    
    Args:
        symbols_data (list): Данные торговых пар
    """
    
    if not symbols_data:
        print("📊 Нет данных для отображения")
        return
    
    print(f"\\n📊 ИНФОРМАЦИЯ О ТОРГОВЫХ ПАРАХ BITGET")
    print("=" * 100)
    print(f"🔢 Всего торговых пар: {len(symbols_data)}")
    
    # Группировка по статусу
    online_pairs = [s for s in symbols_data if s.get('status') == 'online']
    offline_pairs = [s for s in symbols_data if s.get('status') != 'online']
    
    print(f"🟢 Активных пар: {len(online_pairs)}")
    print(f"🔴 Неактивных пар: {len(offline_pairs)}")
    
    # Заголовок таблицы
    print(f"\\n{'Символ':^15} {'Базовая':^8} {'Котир.':^8} {'Статус':^8} {'Мин.размер':>12} {'Макс.размер':>15} {'Точн.цены':>10} {'Комиссии':>15}")
    print("-" * 100)
    
    # Показываем только активные пары (первые 20 для читаемости)
    display_pairs = online_pairs[:20] if len(online_pairs) > 20 else online_pairs
    
    # Статистика по базовым валютам
    base_coins_stats = {}
    quote_coins_stats = {}
    
    for symbol in symbols_data:
        try:
            # Извлекаем данные
            symbol_name = symbol.get('symbol', 'N/A')
            base_coin = symbol.get('baseCoin', 'N/A')
            quote_coin = symbol.get('quoteCoin', 'N/A')
            status = symbol.get('status', 'N/A')
            min_trade_amount = symbol.get('minTradeAmount', '0')
            max_trade_amount = symbol.get('maxTradeAmount', '0')
            price_scale = symbol.get('priceScale', '0')
            quantity_scale = symbol.get('quantityScale', '0')
            taker_fee = symbol.get('takerFeeRate', '0')
            maker_fee = symbol.get('makerFeeRate', '0')
            
            # Статистика по валютам
            if base_coin != 'N/A':
                base_coins_stats[base_coin] = base_coins_stats.get(base_coin, 0) + 1
            if quote_coin != 'N/A':
                quote_coins_stats[quote_coin] = quote_coins_stats.get(quote_coin, 0) + 1
            
            # Показываем только первые 20 для читаемости
            if symbol in display_pairs:
                # Эмодзи для статуса
                status_emoji = "🟢" if status == "online" else "🔴"
                status_display = f"{status_emoji}{status}"
                
                # Форматируем комиссии
                fees_display = f"{float(taker_fee)*100:.3f}%/{float(maker_fee)*100:.3f}%"
                
                print(f"{symbol_name:^15} {base_coin:^8} {quote_coin:^8} {status_display:^10} {min_trade_amount:>12} {max_trade_amount:>15} {price_scale:>10} {fees_display:>15}")
                
        except (ValueError, KeyError) as e:
            print(f"❌ Ошибка обработки символа: {e}")
            continue
    
    if len(online_pairs) > 20:
        print(f"... и еще {len(online_pairs) - 20} активных пар")
    
    # Топ базовых валют
    print(f"\\n📈 ТОП БАЗОВЫХ ВАЛЮТ:")
    print("-" * 40)
    sorted_base_coins = sorted(base_coins_stats.items(), key=lambda x: x[1], reverse=True)[:10]
    
    for coin, count in sorted_base_coins:
        print(f"💰 {coin}: {count} пар")
    
    # Топ котируемых валют
    print(f"\\n💵 ТОП КОТИРУЕМЫХ ВАЛЮТ:")
    print("-" * 40)
    sorted_quote_coins = sorted(quote_coins_stats.items(), key=lambda x: x[1], reverse=True)[:10]
    
    for coin, count in sorted_quote_coins:
        print(f"💵 {coin}: {count} пар")
    
    # Анализ комиссий
    if symbols_data:
        try:
            taker_fees = [float(s.get('takerFeeRate', 0)) for s in symbols_data if s.get('takerFeeRate')]
            maker_fees = [float(s.get('makerFeeRate', 0)) for s in symbols_data if s.get('makerFeeRate')]
            
            if taker_fees and maker_fees:
                avg_taker = sum(taker_fees) / len(taker_fees) * 100
                avg_maker = sum(maker_fees) / len(maker_fees) * 100
                
                print(f"\\n💸 АНАЛИЗ КОМИССИЙ:")
                print("-" * 30)
                print(f"📊 Средняя комиссия тейкера: {avg_taker:.4f}%")
                print(f"📊 Средняя комиссия мейкера: {avg_maker:.4f}%")
                print(f"📊 Разброс тейкера: {min(taker_fees)*100:.4f}% - {max(taker_fees)*100:.4f}%")
                print(f"📊 Разброс мейкера: {min(maker_fees)*100:.4f}% - {max(maker_fees)*100:.4f}%")
                
        except Exception as e:
            print(f"❌ Ошибка анализа комиссий: {e}")

def search_symbols(symbols_data, search_term):
    """
    Поиск торговых пар по названию
    
    Args:
        symbols_data (list): Данные торговых пар
        search_term (str): Поисковый термин
    
    Returns:
        list: Найденные торговые пары
    """
    
    if not symbols_data or not search_term:
        return []
    
    search_term = search_term.upper()
    found_symbols = []
    
    for symbol in symbols_data:
        symbol_name = symbol.get('symbol', '').upper()
        base_coin = symbol.get('baseCoin', '').upper()
        quote_coin = symbol.get('quoteCoin', '').upper()
        
        if (search_term in symbol_name or 
            search_term in base_coin or 
            search_term in quote_coin):
            found_symbols.append(symbol)
    
    return found_symbols

def main():
    """Основная функция"""
    print("🚀 Bitget Spot REST API - Get Symbol Info")
    print("=" * 55)
    
    # Получаем информацию о торговых парах
    symbols = get_symbol_info()
    
    if symbols is not None:
        import json
        print("\n� RAW JSON RESPONSE (first 3 symbols):")
        # Показываем только первые 3 символа, так как список очень большой
        print(json.dumps(symbols[:3], indent=2, ensure_ascii=False))
        
        print(f"\n� Всего торговых пар: {len(symbols)}")
        print("💡 Показаны первые 3 из полного списка символов")
        
        # Также покажем краткую статистику
        format_symbol_info_response(symbols)
    else:
        print("❌ Не удалось получить информацию о торговых парах")

if __name__ == "__main__":
    main()
