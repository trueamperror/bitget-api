#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures WebSocket - Ticker Channel

Канал для получения данных тикеров фьючерсов в реальном времени.
Показывает цены, объемы и статистику по фьючерсным контрактам.

МОДИФИЦИРОВАННАЯ ВЕРСИЯ: Выводит оригинальные JSON сообщения от биржи с отступами.
Больше никакого форматирования - только оригинальные поля биржи.

Документация: https://www.bitget.com/api-doc/contract/websocket/public/Tickers-Channel

Структура данных:
- symbol: торговая пара
- lastPr: последняя цена
- bidPr: лучший бид
- askPr: лучший аск
- bidSz: размер лучшего бида
- askSz: размер лучшего аска
- high24h: максимум за 24ч
- low24h: минимум за 24ч
- ts: временная метка
- change24h: изменение за 24ч
- baseVolume: объем в базовой валюте
- quoteVolume: объем в котируемой валюте
- openUtc: цена открытия UTC
- funding: текущая ставка фондирования
- nextFunding: время следующего фондирования
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

class FuturesTickerChannel:
    def __init__(self, config):
        self.config = config
        self.ws = None
        self.symbols = []        
    async def connect(self):
        """Подключение к WebSocket"""
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Используем фьючерсный WebSocket URL
            futures_ws_url = self.config.get('futuresWsURL', 'wss://ws.bitget.com/v2/ws/public')
            
            self.ws = await websockets.connect(
                futures_ws_url,
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10
            )
            print("✅ Подключение к Futures WebSocket установлено")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    async def subscribe_ticker(self, symbol):
        """Подписка на тикер фьючерса"""
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "instType": "USDT-FUTURES",
                    "channel": "ticker",
                    "instId": symbol.upper()
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
            self.symbols.append(symbol.upper())
            print(f"📡 Подписка на тикер фьючерса {symbol}")
    
    def format_ticker_data(self, data):
        """Вывод оригинальных JSON данных от биржи"""
        print(json.dumps(data, indent=4, ensure_ascii=False))
    def show_tickers_summary(self, *args, **kwargs):
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

async def monitor_single_futures():
    """Мониторинг - показывает оригинальные JSON"""
    config = load_config()
    if not config:
        return
    
    print("📊 МОНИТОРИНГ FUTURES ТИКЕРА")
    print("=" * 40)
    
    ticker_client = FuturesTickerChannel(config)
    
    try:
        if not await ticker_client.connect():
            return
        
        symbol = input("💱 Введите символ фьючерса (например, BTCUSDT): ").strip().upper()
        if not symbol:
            symbol = "BTCUSDT"
        
        await ticker_client.subscribe_ticker(symbol)
        
        print(f"🔄 Мониторинг тикера {symbol}...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await ticker_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await ticker_client.disconnect()

async def monitor_multiple_futures():
    """Мониторинг - показывает оригинальные JSON"""
    config = load_config()
    if not config:
        return
    
    print("📊 МОНИТОРИНГ НЕСКОЛЬКИХ FUTURES")
    print("=" * 40)
    
    ticker_client = FuturesTickerChannel(config)
    
    try:
        if not await ticker_client.connect():
            return
        
        symbols_input = input("💱 Введите символы через запятую (например, BTCUSDT,ETHUSDT): ").strip()
        if not symbols_input:
            symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        else:
            symbols = [s.strip().upper() for s in symbols_input.split(',')]
        
        for symbol in symbols:
            await ticker_client.subscribe_ticker(symbol)
            await asyncio.sleep(0.1)
        
        print(f"🔄 Мониторинг {len(symbols)} фьючерсных контрактов...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await ticker_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await ticker_client.disconnect()

async def funding_rates_monitor():
    """Мониторинг - показывает оригинальные JSON"""
    config = load_config()
    if not config:
        return
    
    print("🏦 МОНИТОРИНГ СТАВОК ФОНДИРОВАНИЯ")
    print("=" * 40)
    
    ticker_client = FuturesTickerChannel(config)
    
    try:
        if not await ticker_client.connect():
            return
        
        # Популярные фьючерсы для мониторинга фондирования
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT"]
        
        print(f"🔄 Мониторинг ставок фондирования для {len(symbols)} контрактов...")
        
        for symbol in symbols:
            await ticker_client.subscribe_ticker(symbol)
            await asyncio.sleep(0.1)
        
        duration = input("⏰ Время мониторинга в секундах (по умолчанию 300): ").strip()
        try:
            duration = int(duration) if duration else 300
        except ValueError:
            duration = 300
        
        print(f"🔄 Мониторинг в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(ticker_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\\n⏰ Время мониторинга ({duration} сек) истекло")
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await ticker_client.disconnect()

async def main():
    """Основная функция"""
    print("📊 BITGET FUTURES TICKER CHANNEL (JSON)")
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. 📊 Один фьючерсный контракт")
    print("2. 📈 Несколько контрактов")
    print("3. 🏦 Мониторинг ставок фондирования")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        if choice == "1":
            await monitor_single_futures()
        elif choice == "2":
            await monitor_multiple_futures()
        elif choice == "3":
            await funding_rates_monitor()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")

if __name__ == "__main__":
    asyncio.run(main())
