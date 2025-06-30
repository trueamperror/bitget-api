# -*- coding: utf-8 -*-
"""
Bitget Spot REST API - Get Tickers
Получение информации о тикерах (24h статистика)

Документация: https://www.bitget.com/api-doc/spot/market/Get-All-Tickers

Описание:
Этот скрипт получает информацию о всех тикерах на спот рынке Bitget за последние 24 часа.
Включает цены, объемы торгов, изменения и другую статистику.

Параметры:
Эндпоинт не требует параметров - возвращает данные по всем торговым парам.

Возвращаемые данные:
- symbol: Торговая пара
- high24h: Максимальная цена за 24ч
- low24h: Минимальная цена за 24ч
- close: Цена закрытия (последняя цена)
- quoteVol: Объем в котируемой валюте за 24ч
- baseVol: Объем в базовой валюте за 24ч
- usdtVol: Объем в USDT за 24ч
- ts: Время получения данных
- buyOne: Лучший бид
- sellOne: Лучший аск
- change24h: Изменение цены за 24ч (в процентах)
- openUtc0: Цена открытия UTC 0:00
- changeUtc: Изменение с UTC 0:00
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

def get_tickers():
    """
    Получение тикеров всех торговых пар
    
    Returns:
        list: Список тикеров или None при ошибке
    """
    
    # Формируем URL эндпоинта
    endpoint = f"{BASE_URL}/api/v2/spot/market/tickers"
    
    try:
        print(f"📊 Запрос тикеров...")
        print(f"🌐 Эндпоинт: {endpoint}")
        
        # Выполняем запрос (публичный эндпоинт, не требует аутентификации)
        response = requests.get(endpoint, timeout=10)
        
        # Проверяем статус ответа
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем код ответа Bitget
            if data.get('code') == '00000':
                tickers_data = data.get('data', [])
                if tickers_data:
                    print(f"✅ Получено {len(tickers_data)} тикеров")
                    return tickers_data
                else:
                    print("⚠️ Данные тикеров не найдены")
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

def format_tickers_response(tickers_data):
    """
    Форматирование ответа с тикерами
    
    Args:
        tickers_data (list): Данные тикеров
    """
    
    if not tickers_data:
        print("📊 Нет данных для отображения")
        return
    
    print(f"\\n📊 ТИКЕРЫ BITGET SPOT")
    print("=" * 120)
    print(f"🔢 Всего тикеров: {len(tickers_data)}")
    
    # Заголовок таблицы
    print(f"\\n{'Символ':^15} {'Цена':>12} {'Изм.24ч':>10} {'Макс.24ч':>12} {'Мин.24ч':>12} {'Объем(USDT)':>15} {'Бид':>12} {'Аск':>12}")
    print("-" * 120)
    
    # Фильтруем и сортируем по объему
    valid_tickers = []
    total_volume_usdt = 0
    
    for ticker in tickers_data:
        try:
            symbol = ticker.get('symbol', 'N/A')
            close = float(ticker.get('close', 0))
            high24h = float(ticker.get('high24h', 0))
            low24h = float(ticker.get('low24h', 0))
            usdtVol = float(ticker.get('usdtVol', 0))
            change24h = ticker.get('change24h', '0')
            buyOne = float(ticker.get('buyOne', 0))
            sellOne = float(ticker.get('sellOne', 0))
            
            # Преобразуем изменение в число
            try:
                change_percent = float(change24h)
            except (ValueError, TypeError):
                change_percent = 0
            
            total_volume_usdt += usdtVol
            
            valid_tickers.append({
                'symbol': symbol,
                'close': close,
                'high24h': high24h,
                'low24h': low24h,
                'usdtVol': usdtVol,
                'change24h': change_percent,
                'buyOne': buyOne,
                'sellOne': sellOne
            })
            
        except (ValueError, KeyError) as e:
            print(f"❌ Ошибка обработки тикера: {e}")
            continue
    
    # Сортируем по объему (топ 20)
    sorted_tickers = sorted(valid_tickers, key=lambda x: x['usdtVol'], reverse=True)[:20]
    
    for ticker in sorted_tickers:
        symbol = ticker['symbol']
        close = ticker['close']
        change24h = ticker['change24h']
        high24h = ticker['high24h']
        low24h = ticker['low24h']
        usdtVol = ticker['usdtVol']
        buyOne = ticker['buyOne']
        sellOne = ticker['sellOne']
        
        # Эмодзи для изменения цены
        change_emoji = "🟢" if change24h >= 0 else "🔴"
        change_display = f"{change_emoji}{change24h:+.2f}%"
        
        print(f"{symbol:^15} {close:>12.6f} {change_display:^12} {high24h:>12.6f} {low24h:>12.6f} {usdtVol:>15,.0f} {buyOne:>12.6f} {sellOne:>12.6f}")
    
    # Общая статистика
    print(f"\\n📈 ОБЩАЯ СТАТИСТИКА:")
    print("-" * 50)
    print(f"💰 Общий объем торгов (24ч): ${total_volume_usdt:,.0f} USDT")
    
    # Анализ изменений
    positive_changes = [t for t in valid_tickers if t['change24h'] > 0]
    negative_changes = [t for t in valid_tickers if t['change24h'] < 0]
    neutral_changes = [t for t in valid_tickers if t['change24h'] == 0]
    
    print(f"🟢 Растущие пары: {len(positive_changes)} ({len(positive_changes)/len(valid_tickers)*100:.1f}%)")
    print(f"🔴 Падающие пары: {len(negative_changes)} ({len(negative_changes)/len(valid_tickers)*100:.1f}%)")
    print(f"⚪ Без изменений: {len(neutral_changes)} ({len(neutral_changes)/len(valid_tickers)*100:.1f}%)")
    
    # Топ растущие
    if positive_changes:
        top_gainers = sorted(positive_changes, key=lambda x: x['change24h'], reverse=True)[:5]
        print(f"\\n📈 ТОП РАСТУЩИЕ (24ч):")
        print("-" * 40)
        for i, ticker in enumerate(top_gainers, 1):
            print(f"{i}. {ticker['symbol']}: +{ticker['change24h']:.2f}% (${ticker['close']:.6f})")
    
    # Топ падающие
    if negative_changes:
        top_losers = sorted(negative_changes, key=lambda x: x['change24h'])[:5]
        print(f"\\n📉 ТОП ПАДАЮЩИЕ (24ч):")
        print("-" * 40)
        for i, ticker in enumerate(top_losers, 1):
            print(f"{i}. {ticker['symbol']}: {ticker['change24h']:.2f}% (${ticker['close']:.6f})")
    
    # Топ по объему
    top_volume = sorted(valid_tickers, key=lambda x: x['usdtVol'], reverse=True)[:5]
    print(f"\\n💰 ТОП ПО ОБЪЕМУ (24ч):")
    print("-" * 50)
    for i, ticker in enumerate(top_volume, 1):
        print(f"{i}. {ticker['symbol']}: ${ticker['usdtVol']:,.0f} USDT")
    
    # Анализ спредов
    spreads = []
    for ticker in valid_tickers:
        if ticker['buyOne'] > 0 and ticker['sellOne'] > 0:
            spread = (ticker['sellOne'] - ticker['buyOne']) / ticker['buyOne'] * 100
            spreads.append(spread)
    
    if spreads:
        avg_spread = sum(spreads) / len(spreads)
        min_spread = min(spreads)
        max_spread = max(spreads)
        
        print(f"\\n📊 АНАЛИЗ СПРЕДОВ:")
        print("-" * 30)
        print(f"📊 Средний спред: {avg_spread:.4f}%")
        print(f"📊 Минимальный спред: {min_spread:.4f}%")
        print(f"📊 Максимальный спред: {max_spread:.4f}%")

def get_specific_ticker(symbol):
    """
    Получение тикера конкретной торговой пары
    
    Args:
        symbol (str): Символ торговой пары (например, BTCUSDT)
    
    Returns:
        dict: Данные тикера или None при ошибке
    """
    
    endpoint = f"{BASE_URL}/api/v2/spot/market/ticker"
    params = {'symbol': symbol}
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '00000':
                return data.get('data')
        
        return None
        
    except Exception:
        return None

def main():
    """Основная функция"""
    print("📊 Bitget Spot REST API - Get Tickers")
    print("=" * 55)
    
    # Получаем все тикеры
    tickers = get_tickers()
    
    if tickers is not None:
        import json
        print("\n📄 RAW JSON RESPONSE (first 3 tickers):")
        # Показываем только первые 3 тикера, так как список очень большой
        print(json.dumps(tickers[:3], indent=2, ensure_ascii=False))
        
        print(f"\n� Всего тикеров: {len(tickers)}")
        print("� Показаны первые 3 из полного списка тикеров")
        
        # Также покажем краткую статистику  
        format_tickers_response(tickers)
    else:
        print("❌ Не удалось получить тикеры")
        print("❌ Не удалось получить тикеры")

if __name__ == "__main__":
    main()
