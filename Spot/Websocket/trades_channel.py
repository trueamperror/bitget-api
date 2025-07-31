#!/usr/bin/env python3
"""
Bitget Spot WebSocket - Trades Channel

Канал для получения данных о сделках в реальном времени.
Показывает каждую совершенную сделку с деталями.

МОДИФИЦИРОВАННАЯ ВЕРСИЯ: Выводит оригинальные JSON сообщения от биржи с отступами.
Больше никакого форматирования - только оригинальные поля биржи.

Документация: https://www.bitget.com/api-doc/spot/websocket/public/Trades-Channel

Структура данных:
- symbol: торговая пара
- tradeId: ID сделки
- side: сторона (buy/sell)
- fillPrice: цена исполнения
- fillQuantity: количество
- fillTime: время исполнения
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

class SpotTradesChannel:
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
            
            self.ws = await websockets.connect(
                self.config['wsURL'],
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10
            )
            print("✅ Подключение к Spot WebSocket установлено")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    async def subscribe_trades(self, symbol):
        """Подписка на сделки конкретного символа"""
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "instType": "SPOT",
                    "channel": "trade",
                    "instId": symbol.upper()
                }
            ]
        }
        
        await self.ws.send(json.dumps(subscribe_message))
        self.symbols.append(symbol.upper())
        print(f"📡 Подписка на сделки {symbol}")
    
    def format_trade_data(self, data):
        """Вывод оригинальных JSON данных от биржи"""
        print(json.dumps(data, indent=4, ensure_ascii=False))
    
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

async def monitor_single_symbol():
    """Мониторинг - показывает оригинальные JSON"""
    config = load_config()
    if not config:
        return
    
    print("💥 МОНИТОРИНГ СДЕЛОК ОДНОГО СИМВОЛА")
    print("=" * 40)
    
    trades_client = SpotTradesChannel(config)
    
    try:
        if not await trades_client.connect():
            return
        
        symbol = input("💱 Введите символ для мониторинга (например, BTCUSDT): ").strip().upper()
        if not symbol:
            symbol = "BTCUSDT"
        
        await trades_client.subscribe_trades(symbol)
        
        print(f"🔄 Мониторинг сделок {symbol} в реальном времени...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await trades_client.listen()
        
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен")
    finally:
        await trades_client.disconnect()

async def monitor_multiple_symbols():
    """Мониторинг - показывает оригинальные JSON"""
    config = load_config()
    if not config:
        return
    
    print("💥 МОНИТОРИНГ СДЕЛОК НЕСКОЛЬКИХ СИМВОЛОВ")
    print("=" * 40)
    
    trades_client = SpotTradesChannel(config)
    
    try:
        if not await trades_client.connect():
            return
        
        symbols_input = input("💱 Введите символы через запятую (например, BTCUSDT,ETHUSDT): ").strip()
        if not symbols_input:
            symbols_input = "BTCUSDT,ETHUSDT"
        
        symbols = [s.strip().upper() for s in symbols_input.split(',')]
        
        for symbol in symbols:
            await trades_client.subscribe_trades(symbol)
            await asyncio.sleep(0.5)
        
        print(f"🔄 Мониторинг сделок: {', '.join(symbols)}")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await trades_client.listen()
        
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен")
    finally:
        await trades_client.disconnect()

async def trading_activity_monitor():
    """Мониторинг - показывает оригинальные JSON"""
    config = load_config()
    if not config:
        return
    
    print("📊 МОНИТОРИНГ ТОРГОВОЙ АКТИВНОСТИ")
    print("=" * 40)
    
    trades_client = SpotTradesChannel(config)
    
    try:
        if not await trades_client.connect():
            return
        
        symbol = input("💱 Введите символ (например, BTCUSDT): ").strip().upper()
        if not symbol:
            symbol = "BTCUSDT"
        
        duration = input("⏰ Время мониторинга в секундах (по умолчанию 60): ").strip()
        try:
            duration = int(duration) if duration else 60
        except ValueError:
            duration = 60
        
        await trades_client.subscribe_trades(symbol)
        
        print(f"🔄 Мониторинг торговой активности {symbol} в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        # Мониторинг с таймаутом
        try:
            await asyncio.wait_for(trades_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\n⏰ Время мониторинга ({duration} сек) истекло")
        
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен")
    finally:
        await trades_client.disconnect()

async def main():
    """Основная функция"""
    print("💥 BITGET SPOT TRADES CHANNEL (JSON)")
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. 💥 Один символ")
    print("2. 📈 Несколько символов")
    print("3. 📊 Торговая активность (с таймером)")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        if choice == "1":
            await monitor_single_symbol()
        elif choice == "2":
            await monitor_multiple_symbols()
        elif choice == "3":
            await trading_activity_monitor()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\n👋 Программа остановлена")

if __name__ == "__main__":
    asyncio.run(main())
