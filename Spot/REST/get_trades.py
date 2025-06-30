#!/usr/bin/env python3
"""
Bitget API - История сделок пользователя (Spot)
Получение истории исполненных сделок (fills)

Официальная документация:
https://www.bitget.com/api-doc/spot/trade/Get-Fills

Требует аутентификации: Да
Лимит запросов: 10 запросов/секунду
"""

import requests
import json
import hmac
import hashlib
import base64
import time
from datetime import datetime, timedelta

def load_config():
    """Загрузка конфигурации из файла"""
    try:
        with open('../../config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл config.json не найден!")
        print("📝 Создайте файл config.json с вашими API ключами")
        return None
    except json.JSONDecodeError:
        print("❌ Ошибка в формате файла config.json!")
        return None

def create_signature(timestamp, method, request_path, query_string, body, secret_key):
    """Создание подписи для аутентификации"""
    if query_string:
        message = f"{timestamp}{method.upper()}{request_path}?{query_string}{body}"
    else:
        message = f"{timestamp}{method.upper()}{request_path}{body}"
    
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    return base64.b64encode(signature).decode('utf-8')

def get_trade_fills(config, symbol=None, start_time=None, end_time=None, limit=100):
    """
    Получение истории сделок пользователя
    
    Параметры:
    - symbol: Торговая пара (например, 'BTCUSDT'). Если None - все пары
    - start_time: Начальное время (timestamp в ms)
    - end_time: Конечное время (timestamp в ms)
    - limit: Количество записей (1-100)
    """
    
    # Подготовка параметров запроса
    params = {
        'limit': str(min(limit, 100))  # Максимум 100 записей за запрос
    }
    
    if symbol:
        params['symbol'] = symbol.upper()
    
    if start_time:
        params['startTime'] = str(start_time)
        
    if end_time:
        params['endTime'] = str(end_time)
    
    # Формирование строки запроса
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    
    # Параметры для подписи
    timestamp = str(int(time.time() * 1000))
    method = 'GET'
    request_path = '/api/v2/spot/trade/fills'
    body = ''
    
    # Создание подписи
    signature = create_signature(timestamp, method, request_path, query_string, body, config['secretKey'])
    
    # Заголовки запроса
    headers = {
        'ACCESS-KEY': config['apiKey'],
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': config['passphrase'],
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }
    
    # URL запроса
    url = f"{config['baseURL']}{request_path}?{query_string}"
    
    try:
        print(f"🔄 Запрос истории сделок...")
        if symbol:
            print(f"💱 Пара: {symbol}")
        
        response = requests.get(url, headers=headers, timeout=config.get('timeout', 30))
        
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

def format_side(side):
    """Форматирование стороны сделки"""
    if side.lower() == 'buy':
        return '🟢 Покупка'
    elif side.lower() == 'sell':
        return '🔴 Продажа'
    else:
        return f"❓ {side}"

def format_fee_currency(fee_currency):
    """Форматирование валюты комиссии"""
    if not fee_currency:
        return "N/A"
    
    currency_emojis = {
        'USDT': '💵',
        'BTC': '🟡',
        'ETH': '🔷',
        'BNB': '🟨',
        'USDC': '💶'
    }
    
    emoji = currency_emojis.get(fee_currency.upper(), '💰')
    return f"{emoji} {fee_currency}"

def analyze_trades(trades):
    """Анализ торговых сделок"""
    if not trades:
        return
    
    print(f"\n📊 АНАЛИЗ СДЕЛОК")
    print("=" * 50)
    
    # Общая статистика
    total_buy_volume = 0
    total_sell_volume = 0
    total_buy_qty = 0
    total_sell_qty = 0
    total_fees = 0
    symbols_traded = set()
    currencies_traded = set()
    
    buy_count = 0
    sell_count = 0
    
    for trade in trades:
        side = trade.get('side', '').lower()
        notional = float(trade.get('notional', 0))
        base_volume = float(trade.get('baseVolume', 0))
        fee = float(trade.get('fee', 0))
        
        symbols_traded.add(trade.get('symbol', ''))
        currencies_traded.add(trade.get('feeCcy', ''))
        
        total_fees += abs(fee)
        
        if side == 'buy':
            buy_count += 1
            total_buy_volume += notional
            total_buy_qty += base_volume
        elif side == 'sell':
            sell_count += 1
            total_sell_volume += notional
            total_sell_qty += base_volume
    
    total_volume = total_buy_volume + total_sell_volume
    
    print(f"💰 Общий объем торгов: ${total_volume:,.2f}")
    print(f"🟢 Покупки: {buy_count} сделок, ${total_buy_volume:,.2f}")
    print(f"🔴 Продажи: {sell_count} сделок, ${total_sell_volume:,.2f}")
    print(f"💸 Общие комиссии: ${total_fees:.6f}")
    print(f"💱 Торговых пар: {len(symbols_traded)}")
    
    # Средний размер сделки
    if len(trades) > 0:
        avg_trade_size = total_volume / len(trades)
        print(f"📊 Средний размер сделки: ${avg_trade_size:.2f}")
    
    # Топ торговых пар по объему
    if len(symbols_traded) > 1:
        symbol_volume = {}
        symbol_count = {}
        
        for trade in trades:
            symbol = trade.get('symbol', '')
            volume = float(trade.get('notional', 0))
            symbol_volume[symbol] = symbol_volume.get(symbol, 0) + volume
            symbol_count[symbol] = symbol_count.get(symbol, 0) + 1
        
        print(f"\n💎 Топ торговых пар:")
        sorted_symbols = sorted(symbol_volume.items(), key=lambda x: x[1], reverse=True)
        for i, (symbol, volume) in enumerate(sorted_symbols[:5], 1):
            count = symbol_count[symbol]
            avg_size = volume / count
            print(f"   {i}. {symbol}: ${volume:,.2f} ({count} сделок, ср. ${avg_size:.2f})")
    
    # Анализ комиссий по валютам
    if len(currencies_traded) > 1:
        fee_by_currency = {}
        for trade in trades:
            currency = trade.get('feeCcy', 'UNKNOWN')
            fee = float(trade.get('fee', 0))
            fee_by_currency[currency] = fee_by_currency.get(currency, 0) + abs(fee)
        
        print(f"\n💸 Комиссии по валютам:")
        for currency, fee_total in sorted(fee_by_currency.items(), key=lambda x: x[1], reverse=True):
            formatted_currency = format_fee_currency(currency)
            print(f"   {formatted_currency}: {fee_total:.6f}")

def display_trades(trades):
    """Отображение списка сделок"""
    if not trades:
        print("📭 Нет сделок для отображения")
        return
    
    print(f"\n💼 ИСТОРИЯ СДЕЛОК")
    print("=" * 80)
    print(f"🔢 Найдено сделок: {len(trades)}")
    
    # Заголовок таблицы
    print(f"\n{'Время':<12} {'Пара':<10} {'Сторона':<8} {'Цена':<12} {'Количество':<15} {'Объем USD':<12} {'Комиссия':<10}")
    print("-" * 85)
    
    for trade in trades:
        # Форматирование времени
        trade_time = int(trade.get('cTime', 0))
        if trade_time:
            dt = datetime.fromtimestamp(trade_time / 1000)
            time_str = dt.strftime('%d.%m %H:%M')
        else:
            time_str = "N/A"
        
        # Данные сделки
        symbol = trade.get('symbol', 'N/A')[:10]
        side = '🟢 BUY' if trade.get('side', '').lower() == 'buy' else '🔴 SELL'
        price = float(trade.get('price', 0))
        base_volume = float(trade.get('baseVolume', 0))
        notional = float(trade.get('notional', 0))
        fee = float(trade.get('fee', 0))
        fee_currency = trade.get('feeCcy', '')
        
        # Форматирование для отображения
        price_str = f"${price:.4f}" if price > 0 else "N/A"
        volume_str = f"{base_volume:.6f}".rstrip('0').rstrip('.')
        notional_str = f"${notional:.2f}"
        fee_str = f"{abs(fee):.6f} {fee_currency}" if fee != 0 else "0"
        
        print(f"{time_str:<12} {symbol:<10} {side:<8} {price_str:<12} {volume_str:<15} {notional_str:<12} {fee_str:<10}")

def display_recent_summary(trades):
    """Краткая сводка последних сделок"""
    if not trades:
        return
    
    recent_trades = trades[:5]  # Последние 5 сделок
    
    print(f"\n🔥 ПОСЛЕДНИЕ СДЕЛКИ")
    print("=" * 40)
    
    for i, trade in enumerate(recent_trades, 1):
        trade_time = int(trade.get('cTime', 0))
        if trade_time:
            dt = datetime.fromtimestamp(trade_time / 1000)
            time_str = dt.strftime('%d.%m.%Y %H:%M:%S')
        else:
            time_str = "N/A"
        
        symbol = trade.get('symbol', 'N/A')
        side = format_side(trade.get('side', ''))
        price = float(trade.get('price', 0))
        notional = float(trade.get('notional', 0))
        
        print(f"#{i} [{time_str}]")
        print(f"   💱 {symbol} • {side}")
        print(f"   💰 ${price:.4f} • Объем: ${notional:.2f}")
        print()

def main():
    """Основная функция"""
    print("💼 ИСТОРИЯ СДЕЛОК BITGET SPOT")
    print("=" * 50)
    
    # Загрузка конфигурации
    config = load_config()
    if not config:
        return
    
    # Получение истории сделок без интерактивного ввода
    # Используем последние 7 дней, все пары, лимит 50
    from datetime import timedelta
    start_time = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
    trades = get_trade_fills(config, symbol=None, start_time=start_time, end_time=None, limit=50)
    
    if trades is not None:
        import json
        print("\n📄 RAW JSON RESPONSE:")
        print(json.dumps(trades, indent=2, ensure_ascii=False))
        
        print(f"\n� Найдено сделок за последние 7 дней: {len(trades)}")
        if trades:
            print("� Показана полная история сделок пользователя")
        else:
            print("✅ Нет сделок за указанный период")
    else:
        print("❌ Не удалось получить историю сделок")
    
    period_choice = input("Ваш выбор (1-4): ").strip()
    
    start_time = None
    end_time = None
    
    if period_choice == "1":
        start_time = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
    elif period_choice == "2":
        start_time = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
    elif period_choice == "3":
        start_time = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
    elif period_choice == "4":
        try:
            days = int(input("📅 Количество дней назад: "))
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        except ValueError:
            print("❌ Неверный формат, используем последние 7 дней")
            start_time = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
    
    # Количество сделок
    try:
        limit = int(input("🔢 Количество сделок (1-100, по умолчанию 50): ") or "50")
        limit = max(1, min(limit, 100))
    except ValueError:
        limit = 50
    
    # Получение истории сделок
    trades = get_trade_fills(config, symbol, start_time, end_time, limit)
    
    if trades is not None:
        if trades:
            display_recent_summary(trades)
            display_trades(trades)
            analyze_trades(trades)
        else:
            print("📭 Сделки не найдены за указанный период")
            if symbol:
                print(f"💱 Пара: {symbol}")
    else:
        print("❌ Не удалось получить историю сделок")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("🔧 Проверьте config.json и соединение с интернетом")
