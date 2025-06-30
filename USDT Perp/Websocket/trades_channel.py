#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures WebSocket - Trades Channel

Канал для получения данных о торгах фьючерсов в реальном времени.
Показывает последние сделки с ценами и объемами.

Документация: https://www.bitget.com/api-doc/contract/websocket/public/Trades-Channel

Структура данных:
- tradeId: ID сделки
- price: цена сделки
- size: размер сделки в контрактах
- side: сторона (buy/sell)
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


class FuturesTradesChannel:
    def __init__(self, config):
        self.config = config
        self.ws = None
        self.symbols = []
        self.trade_count = 0
        self.trade_stats = {}
        
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
    
    async def subscribe_trades(self, symbol):
        """Подписка на торги фьючерса"""
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "instType": "USDT-FUTURES",
                    "channel": "trade",
                    "instId": symbol.upper()
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
            self.symbols.append(symbol.upper())
            self.trade_stats[symbol.upper()] = {
                'buy_count': 0,
                'sell_count': 0,
                'buy_volume': 0,
                'sell_volume': 0,
                'buy_value': 0,
                'sell_value': 0,
                'last_price': 0,
                'price_high': 0,
                'price_low': float('inf'),
                'large_trades': 0,  # Сделки > 10000 USDT
                'avg_trade_size': 0
            }
            print(f"📡 Подписка на торги фьючерса {symbol}")
    
    def format_trade_data(self, data):
        """Форматирование данных торгов"""
        if not data or 'data' not in data:
            return
        
        for trade in data['data']:
            self.trade_count += 1
            
            symbol = data.get('arg', {}).get('instId', 'N/A')
            trade_id = trade.get('tradeId', 'N/A')
            price = float(trade.get('price', 0))
            size = float(trade.get('size', 0))  # Размер в контрактах
            side = trade.get('side', 'unknown')
            ts = trade.get('ts', 0)
            
            # Обновляем статистику
            if symbol in self.trade_stats:
                stats = self.trade_stats[symbol]
                stats['last_price'] = price
                stats['price_high'] = max(stats['price_high'], price)
                stats['price_low'] = min(stats['price_low'], price)
                
                # Расчет стоимости в USDT (для фьючерсов размер контракта = стоимость в USD)
                trade_value = price * size
                
                if side == 'buy':
                    stats['buy_count'] += 1
                    stats['buy_volume'] += size
                    stats['buy_value'] += trade_value
                else:
                    stats['sell_count'] += 1
                    stats['sell_volume'] += size
                    stats['sell_value'] += trade_value
                
                # Определение крупной сделки
                if trade_value > 10000:
                    stats['large_trades'] += 1
                
                # Средний размер сделки
                total_trades = stats['buy_count'] + stats['sell_count']
                total_value = stats['buy_value'] + stats['sell_value']
                stats['avg_trade_size'] = total_value / total_trades if total_trades > 0 else 0
            
            # Форматирование времени
            if ts:
                dt = datetime.fromtimestamp(int(ts) / 1000)
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Эмодзи для стороны сделки
            side_emoji = "🟢" if side == "buy" else "🔴"
            side_text = "LONG" if side == "buy" else "SHORT"
            
            # Расчет стоимости
            trade_value = price * size
            
            # Определение размера сделки
            size_indicator = ""
            if trade_value > 50000:
                size_indicator = "🐋"  # Кит
            elif trade_value > 10000:
                size_indicator = "🦈"  # Акула
            elif trade_value > 1000:
                size_indicator = "🐟"  # Рыба
            else:
                size_indicator = "🦐"  # Креветка
            
            print(f"⚡ [{time_str}] FUTURES TRADE #{self.trade_count}")
            print(f"💱 {symbol} │ ID: {trade_id}")
            print(f"{side_emoji} {side_text} │ ${price:,.4f} × {size:,.0f} = ${trade_value:,.2f} {size_indicator}")
            
            # Показываем краткую статистику каждые 25 сделок
            if self.trade_count % 25 == 0:
                self.show_stats(symbol)
            
            print("─" * 60)
    
    def show_stats(self, symbol):
        """Показать статистику торгов"""
        if symbol not in self.trade_stats:
            return
        
        stats = self.trade_stats[symbol]
        total_trades = stats['buy_count'] + stats['sell_count']
        total_volume = stats['buy_volume'] + stats['sell_volume']
        total_value = stats['buy_value'] + stats['sell_value']
        
        if total_trades == 0:
            return
        
        buy_percent = (stats['buy_count'] / total_trades) * 100
        sell_percent = (stats['sell_count'] / total_trades) * 100
        
        buy_value_percent = (stats['buy_value'] / total_value) * 100 if total_value > 0 else 0
        sell_value_percent = (stats['sell_value'] / total_value) * 100 if total_value > 0 else 0
        
        print(f"\\n📊 СТАТИСТИКА FUTURES {symbol}")
        print(f"🔢 Всего сделок: {total_trades}")
        print(f"🟢 Лонги: {stats['buy_count']} ({buy_percent:.1f}%) │ Объем: ${stats['buy_value']:,.0f} ({buy_value_percent:.1f}%)")
        print(f"🔴 Шорты: {stats['sell_count']} ({sell_percent:.1f}%) │ Объем: ${stats['sell_value']:,.0f} ({sell_value_percent:.1f}%)")
        print(f"📈 Макс. цена: ${stats['price_high']:,.4f}")
        print(f"📉 Мин. цена: ${stats['price_low']:,.4f}")
        print(f"💎 Общий объем: {total_volume:,.0f} контрактов (${total_value:,.0f})")
        print(f"🐋 Крупные сделки: {stats['large_trades']} (>${10000:,})")
        print(f"📊 Средний размер: ${stats['avg_trade_size']:,.2f}")
        
        # Индикатор давления
        if buy_value_percent > 60:
            pressure = "🟢 ПОКУПАТЕЛЬСКОЕ ДАВЛЕНИЕ"
        elif sell_value_percent > 60:
            pressure = "🔴 ПРОДАВАТЕЛЬСКОЕ ДАВЛЕНИЕ"
        else:
            pressure = "⚪ СБАЛАНСИРОВАННЫЙ РЫНОК"
        
        print(f"📈 Рыночное давление: {pressure}")
    
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
            
            # Обработка данных торгов
            elif data.get('action') in ['snapshot', 'update']:
                channel = data.get('arg', {}).get('channel', '')
                if channel == 'trade':
                    self.format_trade_data(data)
            
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
            print(f"🔌 Отключение от WebSocket. Всего сделок: {self.trade_count}")
            
            # Финальная статистика
            for symbol in self.symbols:
                self.show_stats(symbol)


async def monitor_single_futures_trades():
    """Мониторинг торгов одного фьючерса"""
    config = load_config()
    if not config:
        return
    
    print("⚡ МОНИТОРИНГ FUTURES ТОРГОВ")
    print("=" * 40)
    
    trades_client = FuturesTradesChannel(config)
    
    try:
        if not await trades_client.connect():
            return
        
        symbol = input("💱 Введите символ фьючерса (например, BTCUSDT): ").strip().upper()
        if not symbol:
            symbol = "BTCUSDT"
        
        await trades_client.subscribe_trades(symbol)
        
        print(f"🔄 Мониторинг торгов {symbol}...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await trades_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await trades_client.disconnect()


async def monitor_multiple_futures_trades():
    """Мониторинг торгов нескольких фьючерсов"""
    config = load_config()
    if not config:
        return
    
    print("⚡ МОНИТОРИНГ FUTURES ТОРГОВ (НЕСКОЛЬКО)")
    print("=" * 40)
    
    trades_client = FuturesTradesChannel(config)
    
    try:
        if not await trades_client.connect():
            return
        
        symbols_input = input("💱 Введите символы через запятую (например, BTCUSDT,ETHUSDT): ").strip()
        if not symbols_input:
            symbols = ["BTCUSDT", "ETHUSDT"]
        else:
            symbols = [s.strip().upper() for s in symbols_input.split(',')]
        
        for symbol in symbols:
            await trades_client.subscribe_trades(symbol)
            await asyncio.sleep(0.1)
        
        print(f"🔄 Мониторинг торгов для {len(symbols)} фьючерсов...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await trades_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await trades_client.disconnect()


async def whale_trades_monitor():
    """Мониторинг крупных сделок (китов)"""
    config = load_config()
    if not config:
        return
    
    print("🐋 МОНИТОРИНГ КРУПНЫХ СДЕЛОК")
    print("=" * 40)
    
    trades_client = FuturesTradesChannel(config)
    
    # Переопределяем метод форматирования для показа только крупных сделок
    original_format = trades_client.format_trade_data
    
    def whale_format_trade_data(data):
        """Показывать только крупные сделки"""
        if not data or 'data' not in data:
            return
        
        for trade in data['data']:
            price = float(trade.get('price', 0))
            size = float(trade.get('size', 0))
            trade_value = price * size
            
            # Показываем только сделки больше 10000 USDT
            if trade_value >= 10000:
                original_format(data)
                break
    
    trades_client.format_trade_data = whale_format_trade_data
    
    try:
        if not await trades_client.connect():
            return
        
        # Мониторим популярные фьючерсы
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        
        for symbol in symbols:
            await trades_client.subscribe_trades(symbol)
            await asyncio.sleep(0.1)
        
        min_amount = input("💰 Минимальная сумма сделки в USDT (по умолчанию 10000): ").strip()
        try:
            min_amount = float(min_amount) if min_amount else 10000
        except ValueError:
            min_amount = 10000
        
        print(f"🔄 Мониторинг крупных сделок (>= ${min_amount:,.0f})...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await trades_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await trades_client.disconnect()


async def market_pressure_analysis():
    """Анализ рыночного давления"""
    config = load_config()
    if not config:
        return
    
    print("📈 АНАЛИЗ РЫНОЧНОГО ДАВЛЕНИЯ")
    print("=" * 40)
    
    trades_client = FuturesTradesChannel(config)
    
    try:
        if not await trades_client.connect():
            return
        
        symbol = input("💱 Введите символ для анализа (например, BTCUSDT): ").strip().upper()
        if not symbol:
            symbol = "BTCUSDT"
        
        duration = input("⏰ Время анализа в секундах (по умолчанию 300): ").strip()
        try:
            duration = int(duration) if duration else 300
        except ValueError:
            duration = 300
        
        await trades_client.subscribe_trades(symbol)
        
        print(f"🔄 Анализ рыночного давления {symbol} в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(trades_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\\n⏰ Анализ завершен ({duration} сек)")
            
            # Детальный анализ
            if symbol in trades_client.trade_stats:
                stats = trades_client.trade_stats[symbol]
                total_value = stats['buy_value'] + stats['sell_value']
                
                if total_value > 0:
                    buy_dominance = (stats['buy_value'] / total_value) * 100
                    sell_dominance = (stats['sell_value'] / total_value) * 100
                    
                    print(f"\\n📊 РЕЗУЛЬТАТЫ АНАЛИЗА:")
                    print(f"🟢 Покупательское давление: {buy_dominance:.2f}%")
                    print(f"🔴 Продавательское давление: {sell_dominance:.2f}%")
                    
                    if buy_dominance > 65:
                        print("🚀 СИЛЬНОЕ ВОСХОДЯЩЕЕ ДАВЛЕНИЕ")
                    elif sell_dominance > 65:
                        print("📉 СИЛЬНОЕ НИСХОДЯЩЕЕ ДАВЛЕНИЕ")
                    else:
                        print("⚖️ СБАЛАНСИРОВАННЫЙ РЫНОК")
                else:
                    print("📭 Недостаточно данных для анализа")
        
    except KeyboardInterrupt:
        print("\\n👋 Анализ остановлен")
    finally:
        await trades_client.disconnect()


async def main():
    """Основная функция"""
    print("⚡ BITGET FUTURES TRADES CHANNEL")
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. ⚡ Один фьючерсный контракт")
    print("2. 📊 Несколько контрактов")
    print("3. 🐋 Мониторинг крупных сделок")
    print("4. 📈 Анализ рыночного давления")
    
    try:
        choice = input("Ваш выбор (1-4): ").strip()
        
        if choice == "1":
            await monitor_single_futures_trades()
        elif choice == "2":
            await monitor_multiple_futures_trades()
        elif choice == "3":
            await whale_trades_monitor()
        elif choice == "4":
            await market_pressure_analysis()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")


if __name__ == "__main__":
    asyncio.run(main())
