#!/usr/bin/env python3
"""
Bitget API - Исторические японские свечи (Spot)
Получение данных японских свечей для технического анализа

Официальная документация:
https://www.bitget.com/api-doc/spot/market/Get-Candle-Data

Требует аутентификации: Нет (публичный эндпоинт)
Лимит запросов: 20 запросов/секунду
"""

import requests
import json
import time
from datetime import datetime, timedelta

def load_config():
    """Загрузка конфигурации из файла"""
    try:
        with open('../../config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл ../../config.json не найден!")
        print("📝 Создайте файл config.json с настройками")
        return None
    except json.JSONDecodeError:
        print("❌ Ошибка в формате файла config.json!")
        return None

def get_candlesticks(config, symbol, granularity='1h', start_time=None, end_time=None, limit=100):
    """
    Получение японских свечей
    
    Параметры:
    - symbol: Торговая пара (обязательно, например 'BTCUSDT')
    - granularity: Временной интервал (1m, 5m, 15m, 30m, 1h, 4h, 6h, 12h, 1day, 1week)
    - start_time: Начальное время (timestamp в ms)
    - end_time: Конечное время (timestamp в ms)
    - limit: Количество свечей (максимум 1000)
    """
    
    # Проверка обязательных параметров
    if not symbol:
        print("❌ Символ торговой пары обязателен!")
        return None
    
    # Подготовка параметров запроса
    params = {
        'symbol': symbol.upper(),
        'granularity': granularity,
        'limit': str(min(limit, 1000))
    }
    
    if start_time:
        params['startTime'] = str(start_time)
        
    if end_time:
        params['endTime'] = str(end_time)
    
    # Формирование строки запроса
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    
    # URL запроса
    url = f"{config['baseURL']}/api/v2/spot/market/candles?{query_string}"
    
    try:
        print(f"🔄 Запрос свечей для {symbol}...")
        print(f"📊 Интервал: {granularity}")
        print(f"🔢 Количество: {limit}")
        
        response = requests.get(url, timeout=config.get('timeout', 30))
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == '00000':
                return data.get('data', [])
            else:
                print(f"❌ Ошибка API: {data.get('msg')}")
                return None
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Превышено время ожидания запроса")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return None
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return None

def parse_candle_data(candles):
    """
    Парсинг данных свечей из формата API
    
    Формат API: [timestamp, open, high, low, close, baseVolume, quoteVolume]
    """
    parsed_candles = []
    
    for candle in candles:
        if len(candle) >= 7:
            parsed_candle = {
                'timestamp': int(candle[0]),
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4]),
                'base_volume': float(candle[5]),
                'quote_volume': float(candle[6]),
                'datetime': datetime.fromtimestamp(int(candle[0]) / 1000)
            }
            parsed_candles.append(parsed_candle)
    
    return parsed_candles

def analyze_price_movement(candles):
    """Анализ движения цены"""
    if len(candles) < 2:
        return
    
    print(f"\n📈 АНАЛИЗ ДВИЖЕНИЯ ЦЕНЫ")
    print("=" * 50)
    
    first_candle = candles[-1]  # Самая старая свеча
    last_candle = candles[0]    # Самая новая свеча
    
    # Изменение цены за период
    price_change = last_candle['close'] - first_candle['open']
    price_change_pct = (price_change / first_candle['open']) * 100
    
    # Максимальная и минимальная цены за период
    highest_price = max([c['high'] for c in candles])
    lowest_price = min([c['low'] for c in candles])
    
    # Средняя цена
    avg_price = sum([c['close'] for c in candles]) / len(candles)
    
    # Волатильность (среднее отклонение)
    volatility = sum([abs(c['high'] - c['low']) for c in candles]) / len(candles)
    volatility_pct = (volatility / avg_price) * 100
    
    # Анализ объемов
    total_volume = sum([c['quote_volume'] for c in candles])
    avg_volume = total_volume / len(candles)
    
    print(f"💰 Начальная цена: ${first_candle['open']:.4f}")
    print(f"💰 Конечная цена: ${last_candle['close']:.4f}")
    
    change_emoji = "🟢" if price_change >= 0 else "🔴"
    print(f"📊 Изменение: {change_emoji} ${price_change:.4f} ({price_change_pct:+.2f}%)")
    
    print(f"📈 Максимум: ${highest_price:.4f}")
    print(f"📉 Минимум: ${lowest_price:.4f}")
    print(f"⚖️ Средняя цена: ${avg_price:.4f}")
    print(f"🌊 Волатильность: ${volatility:.4f} ({volatility_pct:.2f}%)")
    print(f"📊 Общий объем: ${total_volume:,.2f}")
    print(f"📊 Средний объем: ${avg_volume:,.2f}")

def detect_patterns(candles):
    """Поиск простых паттернов"""
    if len(candles) < 3:
        return
    
    print(f"\n🔍 ПОИСК ПАТТЕРНОВ")
    print("=" * 30)
    
    patterns_found = []
    
    # Последние 3 свечи для анализа
    recent_candles = candles[:3]
    
    # Паттерн "Три белых солдата" (три растущих свечи подряд)
    if all(c['close'] > c['open'] for c in recent_candles):
        patterns_found.append("🟢 Три белых солдата (бычий)")
    
    # Паттерн "Три черных ворона" (три падающих свечи подряд)
    elif all(c['close'] < c['open'] for c in recent_candles):
        patterns_found.append("🔴 Три черных ворона (медвежий)")
    
    # Доджи (открытие примерно равно закрытию)
    last_candle = recent_candles[0]
    body_size = abs(last_candle['close'] - last_candle['open'])
    candle_range = last_candle['high'] - last_candle['low']
    
    if candle_range > 0 and (body_size / candle_range) < 0.1:
        patterns_found.append("⭐ Доджи (неопределенность)")
    
    # Молот или повешенный
    if candle_range > 0:
        upper_shadow = last_candle['high'] - max(last_candle['open'], last_candle['close'])
        lower_shadow = min(last_candle['open'], last_candle['close']) - last_candle['low']
        
        if lower_shadow > 2 * body_size and upper_shadow < body_size:
            if last_candle['close'] > last_candle['open']:
                patterns_found.append("🔨 Молот (бычий разворот)")
            else:
                patterns_found.append("🪓 Повешенный (медвежий разворот)")
    
    # Анализ тренда
    if len(candles) >= 5:
        prices = [c['close'] for c in candles[:5]]
        if all(prices[i] > prices[i+1] for i in range(len(prices)-1)):
            patterns_found.append("📈 Восходящий тренд")
        elif all(prices[i] < prices[i+1] for i in range(len(prices)-1)):
            patterns_found.append("📉 Нисходящий тренд")
        else:
            patterns_found.append("📊 Боковое движение")
    
    if patterns_found:
        for pattern in patterns_found:
            print(f"   {pattern}")
    else:
        print("   ❓ Явных паттернов не обнаружено")

def calculate_indicators(candles):
    """Расчет простых технических индикаторов"""
    if len(candles) < 20:
        print("⚠️ Недостаточно данных для расчета индикаторов (нужно минимум 20 свечей)")
        return
    
    print(f"\n🧮 ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ")
    print("=" * 40)
    
    prices = [c['close'] for c in candles]
    
    # Простая скользящая средняя (SMA)
    sma_10 = sum(prices[:10]) / 10
    sma_20 = sum(prices[:20]) / 20
    
    current_price = prices[0]
    
    print(f"📊 Текущая цена: ${current_price:.4f}")
    print(f"📈 SMA(10): ${sma_10:.4f}")
    print(f"📈 SMA(20): ${sma_20:.4f}")
    
    # Позиция цены относительно скользящих средних
    if current_price > sma_10 > sma_20:
        print("🟢 Цена выше обеих SMA (бычий сигнал)")
    elif current_price < sma_10 < sma_20:
        print("🔴 Цена ниже обеих SMA (медвежий сигнал)")
    else:
        print("🟡 Смешанные сигналы от SMA")
    
    # RSI упрощенный (на основе последних изменений)
    if len(candles) >= 14:
        changes = []
        for i in range(13):
            change = candles[i]['close'] - candles[i+1]['close']
            changes.append(change)
        
        gains = [c for c in changes if c > 0]
        losses = [abs(c) for c in changes if c < 0]
        
        if gains and losses:
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0.001
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            print(f"📊 RSI(14): {rsi:.1f}")
            if rsi > 70:
                print("🔴 RSI указывает на перекупленность")
            elif rsi < 30:
                print("🟢 RSI указывает на перепроданность")
            else:
                print("🟡 RSI в нормальном диапазоне")

def display_candles(candles, limit_display=10):
    """Отображение свечей в табличном формате"""
    if not candles:
        print("📭 Нет данных свечей для отображения")
        return
    
    print(f"\n🕯️ ЯПОНСКИЕ СВЕЧИ")
    print("=" * 85)
    print(f"🔢 Всего свечей: {len(candles)}")
    print(f"👁️ Показано: {min(limit_display, len(candles))}")
    
    # Заголовок таблицы
    print(f"\n{'Время':<17} {'Открытие':<10} {'Максимум':<10} {'Минимум':<10} {'Закрытие':<10} {'Объем':<12} {'Изм.':<8}")
    print("-" * 85)
    
    display_candles = candles[:limit_display]
    
    for i, candle in enumerate(display_candles):
        # Форматирование времени
        time_str = candle['datetime'].strftime('%d.%m.%Y %H:%M')
        
        # Определение направления свечи
        if candle['close'] > candle['open']:
            change_emoji = "🟢"
            change_pct = ((candle['close'] - candle['open']) / candle['open']) * 100
        elif candle['close'] < candle['open']:
            change_emoji = "🔴"
            change_pct = ((candle['close'] - candle['open']) / candle['open']) * 100
        else:
            change_emoji = "⚪"
            change_pct = 0
        
        # Форматирование объема
        volume_str = f"{candle['quote_volume']:,.0f}"
        if len(volume_str) > 11:
            volume_str = f"{candle['quote_volume']/1000000:.1f}M"
        
        print(f"{time_str:<17} ${candle['open']:<9.4f} ${candle['high']:<9.4f} ${candle['low']:<9.4f} ${candle['close']:<9.4f} {volume_str:<12} {change_emoji}{change_pct:+5.2f}%")

def main():
    """Основная функция"""
    print("🕯️ ЯПОНСКИЕ СВЕЧИ BITGET SPOT")
    print("=" * 50)
    
    # Загрузка конфигурации
    config = load_config()
    if not config:
        return
    
    # Проверка наличия базового URL
    if not config.get('baseURL'):
        print("❌ Отсутствует baseURL в config.json")
        return
    
    # Интерактивный выбор параметров
    print("\n🔧 Настройка запроса:")
    
    # Выбор торговой пары (обязательно)
    symbol = input("💱 Введите символ пары (например, BTCUSDT): ").strip().upper()
    if not symbol:
        print("❌ Символ пары обязателен!")
        return
    
    # Выбор временного интервала
    print("\n📊 Выберите временной интервал:")
    intervals = {
        '1': '1m',   '2': '5m',   '3': '15m',  '4': '30m',
        '5': '1h',   '6': '4h',   '7': '6h',   '8': '12h',
        '9': '1day',  '10': '1week'
    }
    
    print("1. 1 минута    2. 5 минут    3. 15 минут   4. 30 минут")
    print("5. 1 час       6. 4 часа     7. 6 часов    8. 12 часов")
    print("9. 1 день      10. 1 неделя")
    
    interval_choice = input("Ваш выбор (1-10): ").strip()
    granularity = intervals.get(interval_choice, '1h')
    
    # Количество свечей
    try:
        limit = int(input("🔢 Количество свечей (1-1000, по умолчанию 100): ") or "100")
        limit = max(1, min(limit, 1000))
    except ValueError:
        limit = 100
    
    # Опциональные временные рамки
    use_time_range = input("\n📅 Использовать конкретный временной период? (y/n): ").strip().lower()
    
    start_time = None
    end_time = None
    
    if use_time_range == 'y':
        try:
            days_back = int(input("📅 Количество дней назад от текущего момента: "))
            end_time = int(time.time() * 1000)  # Текущее время
            start_time = int((time.time() - (days_back * 24 * 60 * 60)) * 1000)
        except ValueError:
            print("❌ Неверный формат, используем стандартный запрос")
    
    # Получение данных свечей
    candles_raw = get_candlesticks(config, symbol, granularity, start_time, end_time, limit)
    
    if candles_raw is not None:
        # Выводим сырой JSON ответ
        import json
        print("\n📄 RAW JSON RESPONSE:")
        print(json.dumps(candles_raw, indent=2, ensure_ascii=False))
        
        if candles_raw:
            # Парсинг данных
            candles = parse_candle_data(candles_raw)
            
            if candles:
                # Отображение результатов
                display_candles(candles)
                analyze_price_movement(candles)
                detect_patterns(candles)
                calculate_indicators(candles)
            else:
                print("❌ Ошибка при парсинге данных свечей")
        else:
            print("📭 Данные свечей не найдены")
            print(f"💱 Пара: {symbol}")
            print(f"📊 Интервал: {granularity}")
    else:
        print("❌ Не удалось получить данные свечей")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("🔧 Проверьте config.json и соединение с интернетом")
