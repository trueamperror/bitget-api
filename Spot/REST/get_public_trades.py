#!/usr/bin/env python3
"""
Bitget Spot REST API - Get Public Trades

Получение публичных сделок для торговой пары.
Показывает историю последних сделок на рынке.

Документация: https://www.bitget.com/api-doc/spot/market/Get-Recent-Trades

Параметры:
- symbol: торговая пара (обязательный)
- limit: количество записей (1-100, по умолчанию 100)
"""

import requests
import json
from datetime import datetime


def load_config():
    """Загрузка конфигурации из файла"""
    try:
        with open('/Users/timurbogatyrev/Documents/VS Code/Algo/ExchangeAPI/Bitget/config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл config.json не найден!")
        return None


def get_public_trades(symbol="BTCUSDT", limit=50):
    """
    Получение публичных сделок
    
    Args:
        symbol (str): Торговая пара
        limit (int): Количество записей (1-100)
    
    Returns:
        dict: Ответ API с данными сделок
    """
    config = load_config()
    if not config:
        return None
    
    # Параметры запроса
    params = {
        'symbol': symbol,
        'limit': limit
    }
    
    try:
        # Отправляем запрос
        url = f"{config['baseURL']}/api/v2/spot/market/fills"
        headers = {
            'Content-Type': 'application/json',
            'locale': 'en-US'
        }
        
        print(f"📊 Получение публичных сделок для {symbol}...")
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == '00000':
                trades = data.get('data', [])
                
                print(f"✅ Получено {len(trades)} сделок")
                print("=" * 80)
                
                # Заголовок таблицы
                print(f"{'Время':^20} {'Цена':>12} {'Размер':>15} {'Сторона':^8} {'Сумма':>15}")
                print("-" * 80)
                
                total_volume = 0
                buy_volume = 0
                sell_volume = 0
                
                for trade in trades:
                    # Парсим данные сделки
                    trade_id = trade.get('tradeId', 'N/A')
                    price = float(trade.get('price', 0))
                    size = float(trade.get('size', 0))
                    side = trade.get('side', 'unknown')
                    ts = int(trade.get('ts', 0))
                    
                    # Форматируем время
                    if ts:
                        dt = datetime.fromtimestamp(ts / 1000)
                        time_str = dt.strftime("%H:%M:%S.%f")[:-3]
                    else:
                        time_str = "N/A"
                    
                    # Рассчитываем сумму
                    amount = price * size
                    
                    # Эмодзи для стороны
                    side_emoji = "🟢" if side == "buy" else "🔴"
                    side_display = f"{side_emoji}{side.upper()}"
                    
                    # Выводим строку
                    print(f"{time_str:^20} {price:>12.6f} {size:>15.6f} {side_display:^8} ${amount:>14.2f}")
                    
                    # Статистика
                    total_volume += amount
                    if side == "buy":
                        buy_volume += amount
                    else:
                        sell_volume += amount
                
                print("-" * 80)
                
                # Сводная статистика
                print(f"\\n📈 СТАТИСТИКА СДЕЛОК:")
                print(f"💰 Общий объем: ${total_volume:,.2f}")
                print(f"🟢 Покупки: ${buy_volume:,.2f} ({(buy_volume/total_volume*100):.1f}%)")
                print(f"🔴 Продажи: ${sell_volume:,.2f} ({(sell_volume/total_volume*100):.1f}%)")
                
                if trades:
                    last_price = float(trades[0].get('price', 0))
                    first_price = float(trades[-1].get('price', 0))
                    price_change = last_price - first_price
                    price_change_pct = (price_change / first_price * 100) if first_price > 0 else 0
                    
                    change_emoji = "📈" if price_change >= 0 else "📉"
                    print(f"{change_emoji} Изменение цены: {price_change:+.6f} ({price_change_pct:+.2f}%)")
                    print(f"🎯 Последняя цена: ${last_price:.6f}")
                
                return data
            else:
                print(f"❌ Ошибка API: {data.get('msg', 'Unknown error')}")
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


def get_trades_interactive():
    """Интерактивное получение сделок"""
    print("📊 ПОЛУЧЕНИЕ ПУБЛИЧНЫХ СДЕЛОК")
    print("=" * 40)
    
    # Получаем параметры от пользователя
    symbol = input("💱 Введите торговую пару (по умолчанию BTCUSDT): ").strip().upper()
    if not symbol:
        symbol = "BTCUSDT"
    
    limit_input = input("📊 Количество сделок (1-100, по умолчанию 50): ").strip()
    try:
        limit = int(limit_input) if limit_input else 50
        limit = max(1, min(100, limit))  # Ограничиваем диапазон
    except ValueError:
        limit = 50
    
    print(f"\\n🔍 Запрос сделок для {symbol} (лимит: {limit})")
    return get_public_trades(symbol, limit)


def get_trades_multiple_pairs():
    """Получение сделок для нескольких пар"""
    pairs = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"]
    
    print("📊 СДЕЛКИ ПО НЕСКОЛЬКИМ ПАРАМ")
    print("=" * 50)
    
    for pair in pairs:
        print(f"\\n🔍 Получение данных для {pair}...")
        result = get_public_trades(pair, 10)  # По 10 сделок для каждой пары
        
        if not result:
            print(f"❌ Не удалось получить данные для {pair}")
        
        print("\\n" + "─" * 50)


def analyze_market_sentiment():
    """Анализ настроений рынка по сделкам"""
    print("📈 АНАЛИЗ НАСТРОЕНИЙ РЫНКА")
    print("=" * 40)
    
    symbol = input("💱 Введите торговую пару для анализа (по умолчанию BTCUSDT): ").strip().upper()
    if not symbol:
        symbol = "BTCUSDT"
    
    print(f"\\n🔍 Анализ сделок для {symbol}...")
    
    config = load_config()
    if not config:
        return
    
    # Получаем больше данных для анализа
    params = {
        'symbol': symbol,
        'limit': 100
    }
    
    try:
        url = f"{config['baseURL']}/api/v2/spot/market/fills"
        headers = {
            'Content-Type': 'application/json',
            'locale': 'en-US'
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == '00000':
                trades = data.get('data', [])
                
                if not trades:
                    print("❌ Сделки не найдены")
                    return
                
                # Анализ данных
                buy_count = sum(1 for trade in trades if trade.get('side') == 'buy')
                sell_count = len(trades) - buy_count
                
                buy_volume = sum(float(trade.get('price', 0)) * float(trade.get('size', 0)) 
                               for trade in trades if trade.get('side') == 'buy')
                sell_volume = sum(float(trade.get('price', 0)) * float(trade.get('size', 0)) 
                                for trade in trades if trade.get('side') == 'sell')
                
                total_volume = buy_volume + sell_volume
                
                print(f"\\n📊 АНАЛИЗ {len(trades)} СДЕЛОК:")
                print("=" * 40)
                
                print(f"📈 Количество покупок: {buy_count} ({buy_count/len(trades)*100:.1f}%)")
                print(f"📉 Количество продаж: {sell_count} ({sell_count/len(trades)*100:.1f}%)")
                
                print(f"\\n💰 Объем покупок: ${buy_volume:,.2f} ({buy_volume/total_volume*100:.1f}%)")
                print(f"💸 Объем продаж: ${sell_volume:,.2f} ({sell_volume/total_volume*100:.1f}%)")
                
                # Определяем настроение
                volume_ratio = buy_volume / sell_volume if sell_volume > 0 else float('inf')
                count_ratio = buy_count / sell_count if sell_count > 0 else float('inf')
                
                print(f"\\n🎯 НАСТРОЕНИЕ РЫНКА:")
                if volume_ratio > 1.2 and count_ratio > 1.1:
                    print("🟢 БЫЧЬЕ - Преобладают покупки")
                elif volume_ratio < 0.8 and count_ratio < 0.9:
                    print("🔴 МЕДВЕЖЬЕ - Преобладают продажи")
                else:
                    print("🟡 НЕЙТРАЛЬНОЕ - Баланс покупок и продаж")
                
                # Динамика цены
                if len(trades) >= 2:
                    latest_price = float(trades[0].get('price', 0))
                    oldest_price = float(trades[-1].get('price', 0))
                    price_change = ((latest_price - oldest_price) / oldest_price * 100) if oldest_price > 0 else 0
                    
                    trend_emoji = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"
                    print(f"{trend_emoji} Изменение цены: {price_change:+.2f}%")
                
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")


def main():
    """Основная функция"""
    print("📊 BITGET SPOT - ПУБЛИЧНЫЕ СДЕЛКИ")
    print("=" * 40)
    
    # Получаем публичные сделки без интерактивного ввода
    trades = get_public_trades(symbol="BTCUSDT", limit=50)
    
    if trades:
        import json
        print("\n📄 RAW JSON RESPONSE:")
        print(json.dumps(trades, indent=2, ensure_ascii=False))
        
        print(f"\n📊 Найдено публичных сделок: {len(trades)}")
        if trades:
            print("💡 Показаны последние сделки по паре BTCUSDT")
        else:
            print("✅ Нет данных по сделкам")
    else:
        print("❌ Не удалось получить публичные сделки")


if __name__ == "__main__":
    main()
