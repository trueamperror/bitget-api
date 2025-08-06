#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures WebSocket - Depth Channel

Канал для получения данных стакана заявок фьючерсов в реальном времени.
Показывает лучшие bid/ask цены и объемы для фьючерсных контрактов.

МОДИФИЦИРОВАННАЯ ВЕРСИЯ: Выводит оригинальные JSON сообщения от биржи с отступами.
Больше никакого форматирования - только оригинальные поля биржи.

МОДИФИЦИРОВАННАЯ ВЕРСИЯ: Выводит оригинальные JSON сообщения от биржи с отступами.
Больше никакого форматирования - только оригинальные поля биржи.

Документация: https://www.bitget.com/api-doc/contract/websocket/public/Depth-Channel
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

class FuturesDepthChannel:
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
    
    async def subscribe_depth(self, symbol, depth_level="books5"):
        """
        Подписка на стакан заявок фьючерса
        depth_level: books5, books15, books
        """
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "instType": "USDT-FUTURES",
                    "channel": depth_level,
                    "instId": symbol.upper()
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
            self.symbols.append(symbol.upper())
            print(f"📡 Подписка на стакан фьючерса {symbol} ({depth_level})")
    
    def format_depth_data(self, data):
        """Вывод оригинальных JSON данных от биржи"""
        print(json.dumps(data, indent=4, ensure_ascii=False))
    def show_advanced_stats(self, *args, **kwargs):
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

async def monitor_futures_depth():
    """Мониторинг - показывает оригинальные JSON"""
    config = load_config()
    if not config:
        return
    
    print("📚 МОНИТОРИНГ FUTURES СТАКАНА (JSON)")
    print("=" * 40)
    
    depth_client = FuturesDepthChannel(config)
    
    try:
        if not await depth_client.connect():
            return
        
        symbol = "DOGEUSDT"  # Жёстко заданный символ
        depth_level = "books15"  # Жёстко заданная глубина
        
        await depth_client.subscribe_depth(symbol, depth_level)
        
        print(f"🔄 Показываем оригинальные JSON сообщения для {symbol} ({depth_level})...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await depth_client.listen()
        
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен")
    finally:
        await depth_client.disconnect()

async def liquidity_analysis():
    """Упрощенный трекер - показывает только JSON"""
    config = load_config()
    if not config:
        return
    
    print("💧 JSON ТРЕКЕР ЛИКВИДНОСТИ")
    print("=" * 40)
    
    depth_client = FuturesDepthChannel(config)
    
    try:
        if not await depth_client.connect():
            return
        
        symbol = input("💱 Введите символ для анализа (например, BTCUSDT): ").strip().upper()
        if not symbol:
            symbol = "BTCUSDT"
        
        duration = input("⏰ Время анализа в секундах (по умолчанию 300): ").strip()
        try:
            duration = int(duration) if duration else 300
        except ValueError:
            duration = 300
        
        await depth_client.subscribe_depth(symbol, "books15")
        
        print(f"🔄 Показываем JSON сообщения {symbol} в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(depth_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\n⏰ Анализ завершен ({duration} сек)")
        
    except KeyboardInterrupt:
        print("\n👋 Анализ остановлен")
    finally:
        await depth_client.disconnect()

async def spread_monitoring():
    """Мониторинг - показывает оригинальные JSON"""
    config = load_config()
    if not config:
        return
    
    print("💰 JSON МОНИТОРИНГ СПРЕДА")
    print("=" * 40)
    
    depth_client = FuturesDepthChannel(config)
    
    try:
        if not await depth_client.connect():
            return
        
        symbols_input = input("💱 Введите символы через запятую (например, BTCUSDT,ETHUSDT): ").strip()
        if not symbols_input:
            symbols = ["BTCUSDT", "ETHUSDT"]
        else:
            symbols = [s.strip().upper() for s in symbols_input.split(',')]
        
        for symbol in symbols:
            await depth_client.subscribe_depth(symbol, "books5")
            await asyncio.sleep(0.1)
        
        print(f"🔄 Показываем JSON сообщения для {len(symbols)} фьючерсов...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await depth_client.listen()
        
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен")
    finally:
        await depth_client.disconnect()

async def main():
    """Основная функция"""
    print("📚 BITGET FUTURES DEPTH CHANNEL (JSON)")
    print("=" * 40)
    
    # Запускаем прямо мониторинг стакана
    await monitor_futures_depth()

if __name__ == "__main__":
    asyncio.run(main())
