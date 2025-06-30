#!/usr/bin/env python3
"""
Bitget Spot WebSocket - Ticker Channel (Public)

Канал для получения данных тикеров спот торговли в реальном времени.
Публичный канал, не требует аутентификации.

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
        self.ticker_data = {}
        self.update_count = 0
        self.price_changes = {}
        
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
        """Форматирование данных тикеров"""
        if not data or 'data' not in data:
            return
        
        for ticker in data['data']:
            self.update_count += 1
            
            inst_id = ticker.get('instId', 'N/A')
            last = float(ticker.get('last', 0))
            open_24h = float(ticker.get('open24h', 0))
            high_24h = float(ticker.get('high24h', 0))
            low_24h = float(ticker.get('low24h', 0))
            best_bid = float(ticker.get('bestBid', 0))
            best_ask = float(ticker.get('bestAsk', 0))
            base_volume = float(ticker.get('baseVolume', 0))
            quote_volume = float(ticker.get('quoteVolume', 0))
            change_24h = float(ticker.get('change24h', 0))
            ts = ticker.get('ts', 0)
            
            # Сохраняем предыдущую цену для определения направления
            prev_price = self.ticker_data.get(inst_id, {}).get('last', last)
            
            # Обновляем данные тикера
            self.ticker_data[inst_id] = {
                'last': last,
                'open24h': open_24h,
                'high24h': high_24h,
                'low24h': low_24h,
                'bestBid': best_bid,
                'bestAsk': best_ask,
                'baseVolume': base_volume,
                'quoteVolume': quote_volume,
                'change24h': change_24h,
                'ts': ts,
                'prev_price': prev_price,
                'last_update': datetime.now()
            }
            
            # Направление изменения цены
            if last > prev_price:
                price_direction = "📈"
                price_color = "🟢"
            elif last < prev_price:
                price_direction = "📉" 
                price_color = "🔴"
            else:
                price_direction = "➡️"
                price_color = "⚪"
            
            # Форматирование времени
            if ts:
                dt = datetime.fromtimestamp(int(ts) / 1000)
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Расчет спреда
            spread = best_ask - best_bid if best_ask > 0 and best_bid > 0 else 0
            spread_percent = (spread / last) * 100 if last > 0 else 0
            
            print(f"\\n{price_color} [{time_str}] SPOT TICKER #{self.update_count}")
            print(f"💱 {inst_id}")
            print(f"{price_direction} Цена: ${last:,.6f}")
            print(f"📊 24ч: ${change_24h:+.2f}% (${open_24h:,.6f} → ${last:,.6f})")
            print(f"📈 Макс: ${high_24h:,.6f} │ 📉 Мин: ${low_24h:,.6f}")
            print(f"💰 Бид: ${best_bid:,.6f} │ 💸 Аск: ${best_ask:,.6f}")
            print(f"📏 Спред: ${spread:,.6f} ({spread_percent:.4f}%)")
            print(f"� Объем: {base_volume:,.2f} {inst_id.split('USDT')[0]} (${quote_volume:,.2f})")
            
            # Показываем сводку каждые 10 обновлений
            if self.update_count % 10 == 0:
                self.show_market_summary()
            
            print("─" * 60)
    
    def show_market_summary(self):
        """Показать сводку рынка"""
        if not self.ticker_data:
            return
        
        print(f"\\n📊 СВОДКА РЫНКА SPOT (обновлено: {datetime.now().strftime('%H:%M:%S')})")
        print("=" * 70)
        
        # Топ 5 по объему
        top_volume = sorted(
            self.ticker_data.items(),
            key=lambda x: x[1]['quoteVolume'],
            reverse=True
        )[:5]
        
        print("💰 ТОП 5 ПО ОБЪЕМУ:")
        for symbol, data in top_volume:
            print(f"   {symbol}: ${data['quoteVolume']:,.0f} (${data['last']:,.6f})")
        
        # Топ 5 растущих
        top_gainers = sorted(
            self.ticker_data.items(),
            key=lambda x: x[1]['change24h'],
            reverse=True
        )[:5]
        
        print("\\n🚀 ТОП 5 РАСТУЩИХ:")
        for symbol, data in top_gainers:
            print(f"   {symbol}: +{data['change24h']:.2f}% (${data['last']:,.6f})")
        
        # Топ 5 падающих
        top_losers = sorted(
            self.ticker_data.items(),
            key=lambda x: x[1]['change24h']
        )[:5]
        
        print("\\n📉 ТОП 5 ПАДАЮЩИХ:")
        for symbol, data in top_losers:
            print(f"   {symbol}: {data['change24h']:.2f}% (${data['last']:,.6f})")
        
        print(f"\\n📈 Всего тикеров: {len(self.ticker_data)}")
        print(f"🔄 Всего обновлений: {self.update_count}")
    
    async def handle_message(self, message):
        """Обработка входящих сообщений"""
        try:
            data = json.loads(message)
            
            # Обработка ответа на подписку
            if data.get('event') == 'subscribe':
                if str(data.get('code')) == '0':
                    channel = data.get('arg', {}).get('channel', 'unknown')
                    print(f"✅ Подписка успешна: {channel}")
                else:
                    print(f"❌ Ошибка подписки: {data.get('msg', 'Unknown error')}")
            
            # Обработка данных тикеров
            elif data.get('action') in ['snapshot', 'update']:
                channel = data.get('arg', {}).get('channel', '')
                if channel == 'ticker':
                    self.format_ticker_data(data)
            
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
            
            # Финальная сводка
            self.show_market_summary()


async def monitor_specific_ticker():
    """Мониторинг конкретного тикера"""
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
    print("📈 BITGET SPOT TICKER CHANNEL")
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

