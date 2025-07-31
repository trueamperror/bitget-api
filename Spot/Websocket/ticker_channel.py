#!/usr/bin/env python3
"""
Bitget Spot WebSocket - Ticker Channel (Public)

Канал для получения данных тикеров спот торговли в реальном времени.
Публичный канал, не требует аутентификации.

МОДИФИЦИРОВАННАЯ ВЕРСИЯ: Выводит оригинальные JSON сообщения от биржи с отступами.
Больше никакого форматирования - только оригинальные поля биржи.

Документация: https://www.bitget.com/api-doc/spot/websocket/public/Tickers-Channel

Структура данных:
- instId: торговая пара
- last: последняя цена
- open24h: цена открытия 24ч назад  
- high24h: максимум за 24ч
- low24h: минимум за 24ч
- bestBid: лучший бид
- bestAsk: лучший аск
- baseVolume: объем в базовой валюте за 24ч
- quoteVolume: объем в котируемой валюте за 24ч
- ts: временная метка
- change24h: изменение за 24ч в процентах
"""

import asyncio
import json
import ssl
import websockets
from datetime import datetime

def load_config():
    """Загрузка конфигурации из файла"""
    try:
        with open('/Users/timurbogatyrev/Documents/VS Code/Algo/ExchangeAPI/Bitget/config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл config.json не найден!")
        return None

class SpotTickerChannel:
    def __init__(self, config):
        self.config = config
        self.ws = None        
    async def connect(self):
        """Подключение к WebSocket"""
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Используем публичный WebSocket URL
            public_ws_url = self.config.get('wsURL', 'wss://ws.bitget.com/v2/ws/public')
            
            self.ws = await websockets.connect(
                public_ws_url,
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10
            )
            print("✅ Подключение к Public WebSocket установлено")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    async def subscribe_ticker(self, symbol=None):
        """Подписка на тикеры"""
        if symbol:
            # Подписка на конкретную пару
            subscribe_message = {
                "op": "subscribe",
                "args": [
                    {
                        "instType": "SPOT",
                        "channel": "ticker",
                        "instId": symbol
                    }
                ]
            }
            print(f"📡 Подписка на тикер {symbol}")
        else:
            # Подписка на все тикеры
            subscribe_message = {
                "op": "subscribe", 
                "args": [
                    {
                        "instType": "SPOT",
                        "channel": "ticker",
                        "instId": "default"
                    }
                ]
            }
            print("📡 Подписка на все тикеры")
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
    
    def format_ticker_data(self, data):
        """Вывод оригинальных JSON данных от биржи"""
        print(json.dumps(data, indent=4, ensure_ascii=False))
    def show_market_summary(self, *args, **kwargs):
        """Метод удален - показываем только оригинальные JSON"""
        pass
    async def handle_message(self, message):
        """Обработка входящих сообщений - вывод оригинальных JSON"""
        try:
            data = json.loads(message)
            print(json.dumps(data, indent=4, ensure_ascii=False))
            
            # Пинг-понг
            if 'ping' in data:
                pong_message = {'pong': data['ping']}
                if self.ws:
                    await self.ws.send(json.dumps(pong_message))
        
        except json.JSONDecodeError:
            print(f"❌ Ошибка декодирования JSON: {message}")
        except Exception as e:
            print(f"❌ Ошибка обработки сообщения: {e}")
    async def listen(self):
        """Прослушивание сообщений"""
        try:
            if self.ws:
                async for message in self.ws:
                    await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 WebSocket соединение закрыто")
        except Exception as e:
            print(f"❌ Ошибка прослушивания: {e}")
    
    async def disconnect(self):
        """Отключение от WebSocket"""
        if self.ws:
            await self.ws.close()
            print("🔌 Отключение от WebSocket")

async def monitor_specific_ticker():
    """Мониторинг - показывает оригинальные JSON"""
    config = load_config()
    if not config:
        return
    
    symbol = input("💱 Введите символ (например BTCUSDT) или Enter для всех: ").strip().upper()
    if not symbol:
        symbol = None
    
    print("📈 МОНИТОРИНГ SPOT ТИКЕРОВ")
    print("=" * 40)
    
    ticker_client = SpotTickerChannel(config)
    
    try:
        if not await ticker_client.connect():
            return
        
        await ticker_client.subscribe_ticker(symbol)
        
        print("🔄 Мониторинг тикеров...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await ticker_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await ticker_client.disconnect()

async def market_scanner():
    """Сканер рынка"""
    config = load_config()
    if not config:
        return
    
    print("🔍 СКАНЕР РЫНКА SPOT")
    print("=" * 40)
    
    duration = input("⏰ Время сканирования в секундах (по умолчанию 300): ").strip()
    try:
        duration = int(duration) if duration else 300
    except ValueError:
        duration = 300
    
    ticker_client = SpotTickerChannel(config)
    
    try:
        if not await ticker_client.connect():
            return
        
        await ticker_client.subscribe_ticker()  # Все тикеры
        
        print(f"🔄 Сканирование рынка в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(ticker_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\\n⏰ Сканирование завершено ({duration} сек)")
            
            # Финальный анализ
            if ticker_client.ticker_data:
                print(f"\\n📊 РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ:")
                print(f"💱 Проанализировано пар: {len(ticker_client.ticker_data)}")
                print(f"🔄 Получено обновлений: {ticker_client.update_count}")
                
                # Анализ волатильности
                high_volatility = [
                    (symbol, data) for symbol, data in ticker_client.ticker_data.items()
                    if abs(data['change24h']) > 10
                ]
                
                if high_volatility:
                    print(f"\\n⚡ ВЫСОКАЯ ВОЛАТИЛЬНОСТЬ (>10%):")
                    for symbol, data in high_volatility[:10]:
                        print(f"   {symbol}: {data['change24h']:+.2f}%")
                
                ticker_client.show_market_summary()
            else:
                print("� Данных не получено")
        
    except KeyboardInterrupt:
        print("\\n👋 Сканирование остановлено")
    finally:
        await ticker_client.disconnect()

async def main():
    """Основная функция"""
    print("CHANNEL") (JSON)
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. 📈 Конкретный тикер")
    print("2. 🔍 Сканер рынка")
    
    try:
        choice = input("Ваш выбор (1-2): ").strip()
        
        if choice == "1":
            await monitor_specific_ticker()
        elif choice == "2":
            await market_scanner()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")

if __name__ == "__main__":
    asyncio.run(main())

