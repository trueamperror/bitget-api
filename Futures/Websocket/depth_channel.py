#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures WebSocket - Depth Channel

Канал для получения данных стакана заявок фьючерсов в реальном времени.
Показывает лучшие bid/ask цены и объемы для фьючерсных контрактов.

Документация: https://www.bitget.com/api-doc/contract/websocket/public/Depth-Channel

Структура данных:
- asks: заявки на продажу [цена, количество]
- bids: заявки на покупку [цена, количество]
- ts: временная метка
- checksum: контрольная сумма для валидации
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
        self.update_count = 0
        self.depth_stats = {}
        
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
            self.depth_stats[symbol.upper()] = {
                'spread_history': [],
                'bid_pressure_history': [],
                'ask_pressure_history': [],
                'imbalance_history': [],
                'last_best_bid': 0,
                'last_best_ask': 0
            }
            print(f"📡 Подписка на стакан фьючерса {symbol} ({depth_level})")
    
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
            
            if not asks or not bids:
                continue
            
            # Форматирование времени
            if ts:
                dt = datetime.fromtimestamp(int(ts) / 1000)
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Лучшие цены
            best_ask = float(asks[0][0])
            best_bid = float(bids[0][0])
            best_ask_size = float(asks[0][1])
            best_bid_size = float(bids[0][1])
            
            # Спред
            spread = best_ask - best_bid
            spread_percent = (spread / best_ask) * 100 if best_ask > 0 else 0
            
            # Обновляем статистику
            if symbol in self.depth_stats:
                stats = self.depth_stats[symbol]
                stats['spread_history'].append(spread_percent)
                stats['last_best_bid'] = best_bid
                stats['last_best_ask'] = best_ask
                
                # Ограничиваем историю
                if len(stats['spread_history']) > 100:
                    stats['spread_history'] = stats['spread_history'][-50:]
            
            print(f"\\n📚 [{time_str}] FUTURES ORDER BOOK #{self.update_count}")
            print(f"💱 {symbol}")
            print("=" * 60)
            
            # Отображение asks (продажи) - от низкой цены к высокой
            print("🔴 ASKS (Шорт позиции)")
            print("   Цена          │ Контракты    │ Сумма USDT")
            print("─" * 50)
            
            total_ask_volume = 0
            total_ask_value = 0
            for i, ask in enumerate(asks[:5]):  # Показываем топ 5
                price = float(ask[0])
                size = float(ask[1])
                total = price * size
                total_ask_volume += size
                total_ask_value += total
                
                # Индикатор размера
                size_indicator = ""
                if total > 100000:
                    size_indicator = "🐋"
                elif total > 50000:
                    size_indicator = "🦈"
                elif total > 10000:
                    size_indicator = "🐟"
                
                print(f"   ${price:>12.4f} │ {size:>11.0f} │ ${total:>10.0f} {size_indicator}")
            
            # Спред
            print(f"         💰 СПРЕД: ${spread:.4f} ({spread_percent:.4f}%)")
            
            # Отображение bids (покупки) - от высокой цены к низкой
            print("🟢 BIDS (Лонг позиции)")
            print("   Цена          │ Контракты    │ Сумма USDT")
            print("─" * 50)
            
            total_bid_volume = 0
            total_bid_value = 0
            for i, bid in enumerate(bids[:5]):  # Показываем топ 5
                price = float(bid[0])
                size = float(bid[1])
                total = price * size
                total_bid_volume += size
                total_bid_value += total
                
                # Индикатор размера
                size_indicator = ""
                if total > 100000:
                    size_indicator = "🐋"
                elif total > 50000:
                    size_indicator = "🦈"
                elif total > 10000:
                    size_indicator = "🐟"
                
                print(f"   ${price:>12.4f} │ {size:>11.0f} │ ${total:>10.0f} {size_indicator}")
            
            # Статистика стакана
            bid_ask_ratio = total_bid_value / total_ask_value if total_ask_value > 0 else 0
            imbalance = ((total_bid_value - total_ask_value) / (total_bid_value + total_ask_value)) * 100 if (total_bid_value + total_ask_value) > 0 else 0
            
            print(f"\\n📊 СТАТИСТИКА СТАКАНА")
            print(f"📤 Общий объем asks: {total_ask_volume:,.0f} контрактов (${total_ask_value:,.0f})")
            print(f"📥 Общий объем bids: {total_bid_volume:,.0f} контрактов (${total_bid_value:,.0f})")
            print(f"⚖️ Соотношение bid/ask: {bid_ask_ratio:.3f}")
            print(f"📊 Дисбаланс: {imbalance:+.2f}% ", end="")
            
            # Индикатор давления
            if imbalance > 20:
                print("🟢 (ПОКУПАТЕЛЬСКОЕ ДАВЛЕНИЕ)")
            elif imbalance < -20:
                print("🔴 (ПРОДАВАТЕЛЬСКОЕ ДАВЛЕНИЕ)")
            else:
                print("⚪ (СБАЛАНСИРОВАНО)")
            
            # Показываем расширенную статистику каждые 10 обновлений
            if self.update_count % 10 == 0:
                self.show_advanced_stats(symbol)
    
    def show_advanced_stats(self, symbol):
        """Показать расширенную статистику стакана"""
        if symbol not in self.depth_stats:
            return
        
        stats = self.depth_stats[symbol]
        
        if len(stats['spread_history']) < 5:
            return
        
        print(f"\\n📈 РАСШИРЕННАЯ СТАТИСТИКА {symbol}")
        print("=" * 50)
        
        # Статистика спреда
        recent_spreads = stats['spread_history'][-10:]
        avg_spread = sum(recent_spreads) / len(recent_spreads)
        min_spread = min(recent_spreads)
        max_spread = max(recent_spreads)
        
        print(f"💰 Спред (последние 10):")
        print(f"   Средний: {avg_spread:.4f}%")
        print(f"   Минимум: {min_spread:.4f}%")
        print(f"   Максимум: {max_spread:.4f}%")
        
        # Определение ликвидности
        if avg_spread < 0.01:
            liquidity = "🟢 ОТЛИЧНАЯ"
        elif avg_spread < 0.05:
            liquidity = "🟡 ХОРОШАЯ"
        elif avg_spread < 0.1:
            liquidity = "🟠 СРЕДНЯЯ"
        else:
            liquidity = "🔴 НИЗКАЯ"
        
        print(f"💧 Ликвидность: {liquidity}")
        
        # Текущие лучшие цены
        print(f"📊 Лучшие цены:")
        print(f"   Бид: ${stats['last_best_bid']:,.4f}")
        print(f"   Аск: ${stats['last_best_ask']:,.4f}")
        print(f"   Мид: ${(stats['last_best_bid'] + stats['last_best_ask']) / 2:,.4f}")
    
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
            
            # Финальная статистика
            for symbol in self.symbols:
                self.show_advanced_stats(symbol)


async def monitor_futures_depth():
    """Мониторинг стакана фьючерса"""
    config = load_config()
    if not config:
        return
    
    print("📚 МОНИТОРИНГ FUTURES СТАКАНА")
    print("=" * 40)
    
    depth_client = FuturesDepthChannel(config)
    
    try:
        if not await depth_client.connect():
            return
        
        symbol = input("💱 Введите символ фьючерса (например, BTCUSDT): ").strip().upper()
        if not symbol:
            symbol = "BTCUSDT"
        
        print("📋 Выберите глубину стакана:")
        print("1. 📚 Топ-5 уровней (books5)")
        print("2. 📖 Топ-15 уровней (books15)")
        print("3. 📙 Полный стакан (books)")
        
        depth_choice = input("Ваш выбор (1-3): ").strip()
        
        if depth_choice == "1":
            depth_level = "books5"
        elif depth_choice == "2":
            depth_level = "books15"
        elif depth_choice == "3":
            depth_level = "books"
            print("⚠️ Внимание: Полный стакан содержит много данных!")
            confirm = input("Продолжить? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Отменено")
                return
        else:
            depth_level = "books5"
        
        await depth_client.subscribe_depth(symbol, depth_level)
        
        print(f"🔄 Мониторинг стакана {symbol} ({depth_level})...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await depth_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await depth_client.disconnect()


async def liquidity_analysis():
    """Анализ ликвидности фьючерса"""
    config = load_config()
    if not config:
        return
    
    print("💧 АНАЛИЗ ЛИКВИДНОСТИ FUTURES")
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
        
        print(f"🔄 Анализ ликвидности {symbol} в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(depth_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\\n⏰ Анализ завершен ({duration} сек)")
            
            # Детальный анализ ликвидности
            if symbol in depth_client.depth_stats:
                stats = depth_client.depth_stats[symbol]
                
                if stats['spread_history']:
                    avg_spread = sum(stats['spread_history']) / len(stats['spread_history'])
                    
                    print(f"\\n📊 РЕЗУЛЬТАТЫ АНАЛИЗА ЛИКВИДНОСТИ:")
                    print(f"💰 Средний спред: {avg_spread:.4f}%")
                    print(f"📈 Обновлений стакана: {depth_client.update_count}")
                    
                    if avg_spread < 0.01:
                        print("🟢 ОТЛИЧНАЯ ЛИКВИДНОСТЬ - рекомендуется для крупных сделок")
                    elif avg_spread < 0.05:
                        print("🟡 ХОРОШАЯ ЛИКВИДНОСТЬ - подходит для средних сделок")
                    elif avg_spread < 0.1:
                        print("🟠 СРЕДНЯЯ ЛИКВИДНОСТЬ - осторожность при крупных сделках")
                    else:
                        print("🔴 НИЗКАЯ ЛИКВИДНОСТЬ - высокий риск проскальзывания")
                else:
                    print("📭 Недостаточно данных для анализа")
        
    except KeyboardInterrupt:
        print("\\n👋 Анализ остановлен")
    finally:
        await depth_client.disconnect()


async def spread_monitoring():
    """Мониторинг спреда"""
    config = load_config()
    if not config:
        return
    
    print("💰 МОНИТОРИНГ СПРЕДА FUTURES")
    print("=" * 40)
    
    depth_client = FuturesDepthChannel(config)
    
    # Переопределяем форматирование для фокуса на спреде
    original_format = depth_client.format_depth_data
    
    def spread_focused_format(data):
        """Форматирование с фокусом на спред"""
        if not data or 'data' not in data:
            return
        
        for book_data in data['data']:
            symbol = data.get('arg', {}).get('instId', 'N/A')
            asks = book_data.get('asks', [])
            bids = book_data.get('bids', [])
            
            if not asks or not bids:
                continue
            
            best_ask = float(asks[0][0])
            best_bid = float(bids[0][0])
            spread = best_ask - best_bid
            spread_percent = (spread / best_ask) * 100
            
            time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            print(f"💰 [{time_str}] SPREAD {symbol}")
            print(f"🟢 Бид: ${best_bid:,.4f} │ 🔴 Аск: ${best_ask:,.4f}")
            print(f"📊 Спред: ${spread:.4f} ({spread_percent:.4f}%)")
            print("─" * 40)
    
    depth_client.format_depth_data = spread_focused_format
    
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
        
        print(f"🔄 Мониторинг спреда для {len(symbols)} фьючерсов...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await depth_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await depth_client.disconnect()


async def main():
    """Основная функция"""
    print("📚 BITGET FUTURES DEPTH CHANNEL")
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. 📚 Стакан фьючерса")
    print("2. 💧 Анализ ликвидности")
    print("3. 💰 Мониторинг спреда")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        if choice == "1":
            await monitor_futures_depth()
        elif choice == "2":
            await liquidity_analysis()
        elif choice == "3":
            await spread_monitoring()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")


if __name__ == "__main__":
    asyncio.run(main())
