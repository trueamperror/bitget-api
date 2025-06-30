#!/usr/bin/env python3
"""
Bitget Spot WebSocket - Trades Channel

Канал для получения данных о сделках в реальном времени.
Показывает каждую совершенную сделку с деталями.

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
        self.trade_count = 0
        
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
        """Форматирование данных сделок"""
        if not data or 'data' not in data:
            return
        
        for trade in data['data']:
            self.trade_count += 1
            
            symbol = data.get('arg', {}).get('instId', 'N/A')
            trade_id = trade.get('tradeId', 'N/A')
            side = trade.get('side', 'N/A')
            price = float(trade.get('fillPrice', 0))
            quantity = float(trade.get('fillQuantity', 0))
            fill_time = trade.get('fillTime', 0)
            
            # Форматирование времени
            if fill_time:
                dt = datetime.fromtimestamp(int(fill_time) / 1000)
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Эмодзи для стороны сделки
            side_emoji = "🟢" if side == "buy" else "🔴"
            side_arrow = "↗️" if side == "buy" else "↘️"
            
            # Расчет стоимости сделки
            total_value = price * quantity
            
            print(f"\n💥 [{time_str}] SPOT TRADE #{self.trade_count}")
            print(f"💱 {symbol}")
            print(f"{side_arrow} Сторона: {side_emoji} {side.upper()}")
            print(f"💰 Цена: ${price:,.4f}")
            print(f"📊 Количество: {quantity:,.4f}")
            print(f"💵 Стоимость: ${total_value:,.2f}")
            print(f"🆔 Trade ID: {trade_id}")
    
    async def handle_message(self, message):
        """Обработка входящих сообщений"""
        try:
            data = json.loads(message)
            
            # Обработка ответа на подписку
            if data.get('event') == 'subscribe':
                if data.get('code') == '0':
                    print(f"✅ Подписка успешна: {data.get('arg', {}).get('instId', 'unknown')}")
                else:
                    print(f"❌ Ошибка подписки: {data.get('msg', 'Unknown error')}")
            
            # Обработка данных сделок
            elif data.get('action') == 'snapshot' or data.get('action') == 'update':
                if data.get('arg', {}).get('channel') == 'trade':
                    self.format_trade_data(data)
            
            # Пинг-понг
            elif 'ping' in data:
                pong_message = {'pong': data['ping']}
                await self.ws.send(json.dumps(pong_message))
        
        except json.JSONDecodeError:
            print(f"❌ Ошибка декодирования JSON: {message}")
        except Exception as e:
            print(f"❌ Ошибка обработки сообщения: {e}")
    
    async def listen(self):
        """Прослушивание сообщений"""
        try:
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
            print(f"🔌 Отключение от WebSocket. Всего сделок: {self.trade_count}")


async def monitor_single_symbol():
    """Мониторинг сделок одного символа"""
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
    """Мониторинг сделок нескольких символов"""
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
    """Мониторинг торговой активности с статистикой"""
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
            print(f"📊 Статистика: Зафиксировано {trades_client.trade_count} сделок")
        
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен")
        print(f"📊 Статистика: Зафиксировано {trades_client.trade_count} сделок")
    finally:
        await trades_client.disconnect()


async def main():
    """Основная функция"""
    print("💥 BITGET SPOT TRADES CHANNEL")
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
