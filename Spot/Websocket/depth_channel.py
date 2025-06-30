#!/usr/bin/env python3
"""
Bitget Spot WebSocket - Depth Channel (Order Book)

Канал для получения данных стакана заявок в реальном времени.
Показывает лучшие bid/ask цены и объемы.

Документация: https://www.bitget.com/api-doc/spot/websocket/public/Depth-Channel

Структура данных:
- asks: заявки на продажу [цена, количество]
- bids: заявки на покупку [цена, количество]
- checksum: контрольная сумма для валидации
- ts: временная метка
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


class SpotDepthChannel:
    def __init__(self, config):
        self.config = config
        self.ws = None
        self.symbols = []
        self.update_count = 0
        
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
    
    async def subscribe_depth(self, symbol, depth_level="books5"):
        """
        Подписка на стакан заявок
        depth_level: books5, books15, books
        """
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "instType": "SPOT",
                    "channel": depth_level,
                    "instId": symbol.upper()
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
            self.symbols.append(symbol.upper())
            print(f"📡 Подписка на стакан {symbol} ({depth_level})")
    
    def format_depth_data(self, data):
        """Форматирование данных стакана"""
        if not data or 'data' not in data:
            return
        
        self.update_count += 1
        
        for book_data in data['data']:
            symbol = data.get('arg', {}).get('instId', 'N/A')
            asks = book_data.get('asks', [])
            bids = book_data.get('bids', [])
            ts = book_data.get('ts', 0)
            
            # Форматирование времени
            if ts:
                dt = datetime.fromtimestamp(int(ts) / 1000)
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            print(f"\n📚 [{time_str}] ORDER BOOK #{self.update_count}")
            print(f"💱 {symbol}")
            print("=" * 50)
            
            # Отображение asks (продажи) - от низкой цены к высокой
            print("🔴 ASKS (Продажи)")
            print("   Цена        │ Количество   │ Сумма")
            print("─" * 45)
            
            for i, ask in enumerate(asks[:5]):  # Показываем топ 5
                price = float(ask[0])
                size = float(ask[1])
                total = price * size
                print(f"   ${price:>10.4f} │ {size:>11.4f} │ ${total:>9.2f}")
            
            # Спред
            if asks and bids:
                best_ask = float(asks[0][0])
                best_bid = float(bids[0][0])
                spread = best_ask - best_bid
                spread_percent = (spread / best_ask) * 100
                print(f"         💰 СПРЕД: ${spread:.4f} ({spread_percent:.3f}%)")
            
            # Отображение bids (покупки) - от высокой цены к низкой
            print("🟢 BIDS (Покупки)")
            print("   Цена        │ Количество   │ Сумма")
            print("─" * 45)
            
            for i, bid in enumerate(bids[:5]):  # Показываем топ 5
                price = float(bid[0])
                size = float(bid[1])
                total = price * size
                print(f"   ${price:>10.4f} │ {size:>11.4f} │ ${total:>9.2f}")
            
            # Статистика
            total_ask_volume = sum(float(ask[1]) for ask in asks)
            total_bid_volume = sum(float(bid[1]) for bid in bids)
            
            print(f"\n📊 СТАТИСТИКА")
            print(f"📤 Общий объем asks: {total_ask_volume:.4f}")
            print(f"📥 Общий объем bids: {total_bid_volume:.4f}")
            print(f"⚖️ Соотношение bid/ask: {total_bid_volume/total_ask_volume:.3f}")
    
    async def handle_message(self, message):
        """Обработка входящих сообщений"""
        try:
            data = json.loads(message)
            
            # Обработка ответа на подписку
            if data.get('event') == 'subscribe':
                if data.get('code') == '0':
                    channel = data.get('arg', {}).get('channel', 'unknown')
                    symbol = data.get('arg', {}).get('instId', 'unknown')
                    print(f"✅ Подписка успешна: {symbol} ({channel})")
                else:
                    print(f"❌ Ошибка подписки: {data.get('msg', 'Unknown error')}")
            
            # Обработка данных стакана
            elif data.get('action') == 'snapshot' or data.get('action') == 'update':
                channel = data.get('arg', {}).get('channel', '')
                if 'books' in channel:
                    self.format_depth_data(data)
            
            # Пинг-понг
            elif 'ping' in data:
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
            print(f"🔌 Отключение от WebSocket. Обновлений: {self.update_count}")


async def monitor_top5_depth():
    """Мониторинг топ-5 уровней стакана"""
    config = load_config()
    if not config:
        return
    
    print("📚 МОНИТОРИНГ СТАКАНА (ТОП-5)")
    print("=" * 40)
    
    depth_client = SpotDepthChannel(config)
    
    try:
        if not await depth_client.connect():
            return
        
        symbol = input("💱 Введите символ (например, BTCUSDT): ").strip().upper()
        if not symbol:
            symbol = "BTCUSDT"
        
        await depth_client.subscribe_depth(symbol, "books5")
        
        print(f"🔄 Мониторинг стакана {symbol} (топ-5 уровней)...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await depth_client.listen()
        
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен")
    finally:
        await depth_client.disconnect()


async def monitor_full_depth():
    """Мониторинг полного стакана"""
    config = load_config()
    if not config:
        return
    
    print("📚 МОНИТОРИНГ ПОЛНОГО СТАКАНА")
    print("=" * 40)
    print("⚠️ Внимание: Полный стакан может содержать много данных!")
    
    confirm = input("Продолжить? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Отменено")
        return
    
    depth_client = SpotDepthChannel(config)
    
    try:
        if not await depth_client.connect():
            return
        
        symbol = input("💱 Введите символ (например, BTCUSDT): ").strip().upper()
        if not symbol:
            symbol = "BTCUSDT"
        
        await depth_client.subscribe_depth(symbol, "books")
        
        print(f"🔄 Мониторинг полного стакана {symbol}...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await depth_client.listen()
        
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен")
    finally:
        await depth_client.disconnect()


async def spread_monitoring():
    """Мониторинг спреда"""
    config = load_config()
    if not config:
        return
    
    print("💰 МОНИТОРИНГ СПРЕДА")
    print("=" * 40)
    
    depth_client = SpotDepthChannel(config)
    
    try:
        if not await depth_client.connect():
            return
        
        symbol = input("💱 Введите символ (например, BTCUSDT): ").strip().upper()
        if not symbol:
            symbol = "BTCUSDT"
        
        duration = input("⏰ Время мониторинга в секундах (по умолчанию 60): ").strip()
        try:
            duration = int(duration) if duration else 60
        except ValueError:
            duration = 60
        
        await depth_client.subscribe_depth(symbol, "books5")
        
        print(f"🔄 Мониторинг спреда {symbol} в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(depth_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\n⏰ Время мониторинга ({duration} сек) истекло")
        
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен")
    finally:
        await depth_client.disconnect()


async def main():
    """Основная функция"""
    print("📚 BITGET SPOT DEPTH CHANNEL")
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. 📚 Стакан топ-5 уровней")
    print("2. 📖 Полный стакан")
    print("3. 💰 Мониторинг спреда")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        if choice == "1":
            await monitor_top5_depth()
        elif choice == "2":
            await monitor_full_depth()
        elif choice == "3":
            await spread_monitoring()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\n👋 Программа остановлена")


if __name__ == "__main__":
    asyncio.run(main())
