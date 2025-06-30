#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures WebSocket - Ticker Channel

Канал для получения данных тикеров фьючерсов в реальном времени.
Показывает цены, объемы и статистику по фьючерсным контрактам.

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
        self.ticker_data = {}
        self.update_count = 0
        
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
        """Форматирование данных тикера"""
        if not data or 'data' not in data:
            return
        
        for ticker in data['data']:
            self.update_count += 1
            
            symbol = data.get('arg', {}).get('instId', 'N/A')
            last_pr = float(ticker.get('lastPr', 0))
            bid_pr = float(ticker.get('bidPr', 0))
            ask_pr = float(ticker.get('askPr', 0))
            bid_sz = float(ticker.get('bidSz', 0))
            ask_sz = float(ticker.get('askSz', 0))
            high24h = float(ticker.get('high24h', 0))
            low24h = float(ticker.get('low24h', 0))
            change24h = ticker.get('change24h', '0')
            base_volume = float(ticker.get('baseVolume', 0))
            quote_volume = float(ticker.get('quoteVolume', 0))
            open_utc = float(ticker.get('openUtc', 0))
            funding = ticker.get('funding', '0')
            next_funding = ticker.get('nextFunding', 0)
            ts = ticker.get('ts', 0)
            
            # Преобразуем изменение в число
            try:
                change_percent = float(change24h)
            except (ValueError, TypeError):
                change_percent = 0
            
            # Преобразуем фондирование в число
            try:
                funding_rate = float(funding)
            except (ValueError, TypeError):
                funding_rate = 0
            
            # Сохраняем данные
            self.ticker_data[symbol] = {
                'lastPr': last_pr,
                'bidPr': bid_pr,
                'askPr': ask_pr,
                'high24h': high24h,
                'low24h': low24h,
                'change24h': change_percent,
                'baseVolume': base_volume,
                'quoteVolume': quote_volume,
                'funding': funding_rate,
                'nextFunding': next_funding,
                'ts': ts,
                'updated': datetime.now()
            }
            
            # Форматирование времени
            if ts:
                dt = datetime.fromtimestamp(int(ts) / 1000)
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Эмодзи для изменения цены
            change_emoji = "🟢" if change_percent >= 0 else "🔴"
            
            # Спред
            spread = ask_pr - bid_pr if ask_pr > 0 and bid_pr > 0 else 0
            spread_percent = (spread / ask_pr * 100) if ask_pr > 0 else 0
            
            # Время следующего фондирования
            next_funding_str = "N/A"
            if next_funding:
                next_funding_dt = datetime.fromtimestamp(int(next_funding) / 1000)
                next_funding_str = next_funding_dt.strftime("%H:%M:%S")
            
            print(f"\\n📊 [{time_str}] FUTURES TICKER #{self.update_count}")
            print(f"💱 {symbol} 💰 Цена: ${last_pr:,.4f}")
            print(f"{change_emoji} Изменение: {change_percent:+.2f}% │ 📈 Макс: ${high24h:,.4f} │ 📉 Мин: ${low24h:,.4f}")
            print(f"🟢 Бид: ${bid_pr:,.4f} ({bid_sz:,.0f}) │ 🔴 Аск: ${ask_pr:,.4f} ({ask_sz:,.0f})")
            print(f"📊 Спред: ${spread:,.4f} ({spread_percent:.4f}%)")
            print(f"💰 Объем 24ч: {base_volume:,.0f} ({quote_volume:,.0f} USDT)")
            print(f"🏦 Фондирование: {funding_rate:.6f}% │ ⏰ След: {next_funding_str}")
            
            # Показываем сводку каждые 10 обновлений
            if self.update_count % 10 == 0:
                self.show_tickers_summary()
            
            print("─" * 70)
    
    def show_tickers_summary(self):
        """Показать сводку по тикерам"""
        if not self.ticker_data:
            return
        
        print(f"\\n📊 СВОДКА FUTURES ТИКЕРОВ (обновлено: {datetime.now().strftime('%H:%M:%S')})")
        print("=" * 80)
        
        print(f"🔢 Отслеживается контрактов: {len(self.ticker_data)}")
        print(f"📨 Всего обновлений: {self.update_count}")
        
        # Сортируем по изменению цены
        sorted_tickers = sorted(
            self.ticker_data.items(),
            key=lambda x: x[1]['change24h'],
            reverse=True
        )
        
        print(f"\\n{'Контракт':^15} {'Цена':>12} {'Изм.24ч':>10} {'Объем':>15} {'Фонд.':>8}")
        print("─" * 70)
        
        for symbol, data in sorted_tickers:
            last_pr = data['lastPr']
            change24h = data['change24h']
            quote_volume = data['quoteVolume']
            funding = data['funding']
            
            # Эмодзи для изменения
            change_emoji = "🟢" if change24h >= 0 else "🔴"
            change_display = f"{change_emoji}{change24h:+.2f}%"
            
            # Эмодзи для фондирования
            funding_emoji = "🟢" if funding >= 0 else "🔴"
            funding_display = f"{funding_emoji}{funding:.4f}%"
            
            print(f"{symbol:^15} {last_pr:>12.4f} {change_display:^12} {quote_volume:>15,.0f} {funding_display:^10}")
        
        # Статистика изменений
        positive_count = sum(1 for data in self.ticker_data.values() if data['change24h'] > 0)
        negative_count = sum(1 for data in self.ticker_data.values() if data['change24h'] < 0)
        neutral_count = len(self.ticker_data) - positive_count - negative_count
        
        print(f"\\n📈 Статистика изменений:")
        print(f"🟢 Растущие: {positive_count}")
        print(f"🔴 Падающие: {negative_count}")
        print(f"⚪ Нейтральные: {neutral_count}")
        
        # Средняя ставка фондирования
        if self.ticker_data:
            avg_funding = sum(data['funding'] for data in self.ticker_data.values()) / len(self.ticker_data)
            print(f"🏦 Средняя ставка фондирования: {avg_funding:.6f}%")
    
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
            self.show_tickers_summary()


async def monitor_single_futures():
    """Мониторинг одного фьючерсного контракта"""
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
    """Мониторинг нескольких фьючерсных контрактов"""
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
    """Мониторинг ставок фондирования"""
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
    print("📊 BITGET FUTURES TICKER CHANNEL")
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
