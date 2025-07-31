#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures WebSocket - Fills Channel (Private)

Канал для получения данных об исполненных сделках фьючерсов в реальном времени.
Требует аутентификации для получения приватных данных.

МОДИФИЦИРОВАННАЯ ВЕРСИЯ: Выводит оригинальные JSON сообщения от биржи с отступами.
Больше никакого форматирования - только оригинальные поля биржи.

Документация: https://www.bitget.com/api-doc/contract/websocket/private/Fills-Channel

Структура данных:
- tradeId: ID сделки
- orderId: ID ордера
- symbol: торговая пара
- side: сторона (buy/sell)
- fillSize: размер исполнения в контрактах
- fillPrice: цена исполнения
- orderType: тип ордера
- feeAmount: размер комиссии
- feeCoin: валюта комиссии
- fillTime: время исполнения
- leverage: плечо
- marginMode: режим маржи
- reduceOnly: только закрытие позиции
"""

import asyncio
import json
import ssl
import websockets
import hmac
import hashlib
import base64
import time
from datetime import datetime

def load_config():
    """Загрузка конфигурации из файла"""
    try:
        with open('/Users/timurbogatyrev/Documents/VS Code/Algo/ExchangeAPI/Bitget/config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл config.json не найден!")
        return None

class FuturesFillsChannel:
    def __init__(self, config):
        self.config = config
        self.ws = None
        self.fills_data = {}
        self.update_count = 0
        self.trading_stats = {
            'total_fills': 0,
            'long_fills': 0,
            'short_fills': 0,
            'total_volume': 0,
            'total_fees': 0,
            'pairs_traded': set(),
            'avg_leverage': 0,
            'reduce_only_fills': 0
        }
        
    def generate_signature(self, timestamp, method, request_path, body=''):
        """Генерация подписи для аутентификации"""
        message = str(timestamp) + method + request_path + body
        signature = hmac.new(
            self.config['secretKey'].encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    async def connect(self):
        """Подключение к WebSocket"""
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Используем приватный фьючерсный WebSocket URL
            private_futures_ws_url = self.config.get('privateFuturesWsURL', 'wss://ws.bitget.com/v2/ws/private')
            
            self.ws = await websockets.connect(
                private_futures_ws_url,
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10
            )
            print("✅ Подключение к Private Futures WebSocket установлено")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    async def authenticate(self):
        """Аутентификация для приватных каналов"""
        timestamp = str(int(time.time()))
        method = 'GET'
        request_path = '/user/verify'
        
        signature = self.generate_signature(timestamp, method, request_path)
        
        auth_message = {
            "op": "login",
            "args": [
                {
                    "apiKey": self.config['apiKey'],
                    "passphrase": self.config['passphrase'],
                    "timestamp": timestamp,
                    "sign": signature
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(auth_message))
            print("🔐 Отправлен запрос аутентификации...")
            
            # Ждем ответ аутентификации
            try:
                response = await asyncio.wait_for(self.ws.recv(), timeout=10)
                data = json.loads(response)
                if data.get('event') == 'login':
                    if str(data.get('code')) == '0':  # Преобразуем в строку для сравнения
                        print("✅ Аутентификация успешна!")
                        return True
                    else:
                        print(f"❌ Ошибка аутентификации: {data.get('msg', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ Неожиданный ответ: {data}")
                    return False
            except asyncio.TimeoutError:
                print("❌ Таймаут аутентификации")
                return False
            except Exception as e:
                print(f"❌ Ошибка при получении ответа аутентификации: {e}")
                return False
        
        return False
    
    async def subscribe_fills(self, symbol=None):
        """Подписка на исполнения фьючерсов"""
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "instType": "USDT-FUTURES",
                    "channel": "fills",
                    "instId": symbol if symbol else "default"
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
            if symbol:
                print(f"📡 Подписка на исполнения фьючерса {symbol}")
            else:
                print("📡 Подписка на все исполнения фьючерсов")
    
    def format_fill_data(self, data):
        """Форматирование данных исполнений"""
        if not data or 'data' not in data:
            return
        
        for fill in data['data']:
            self.update_count += 1
            
            trade_id = fill.get('tradeId', 'N/A')
            order_id = fill.get('orderId', 'N/A')
            symbol = fill.get('symbol', 'N/A')
            side = fill.get('side', 'N/A')
            fill_size = float(fill.get('fillSize', 0))
            fill_price = float(fill.get('fillPrice', 0))
            order_type = fill.get('orderType', 'N/A')
            fee_amount = float(fill.get('feeAmount', 0))
            fee_coin = fill.get('feeCoin', 'N/A')
            fill_time = fill.get('fillTime', 0)
            leverage = float(fill.get('leverage', 0))
            margin_mode = fill.get('marginMode', 'N/A')
            reduce_only = fill.get('reduceOnly', False)
            
            # Обновляем статистику
            self.update_trading_stats(symbol, side, fill_size, fill_price, fee_amount, leverage, reduce_only)
            
            # Сохраняем данные исполнения
            self.fills_data[trade_id] = {
                'orderId': order_id,
                'symbol': symbol,
                'side': side,
                'fillSize': fill_size,
                'fillPrice': fill_price,
                'orderType': order_type,
                'feeAmount': fee_amount,
                'feeCoin': fee_coin,
                'fillTime': fill_time,
                'leverage': leverage,
                'marginMode': margin_mode,
                'reduceOnly': reduce_only,
                'timestamp': datetime.now()
            }
            
            # Форматирование времени
            if fill_time:
                dt = datetime.fromtimestamp(int(fill_time) / 1000)
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Эмодзи для стороны сделки
            if side.lower() == 'buy':
                side_emoji = "📈"
                side_text = "LONG"
            else:
                side_emoji = "📉"
                side_text = "SHORT"
            
            # Расчет стоимости исполнения (в фьючерсах размер = количество контрактов)
            fill_value = fill_price * fill_size
            
            # Определение размера сделки
            size_indicator = ""
            if fill_value > 100000:
                size_indicator = "🐋"  # Кит
            elif fill_value > 50000:
                size_indicator = "🦈"  # Акула
            elif fill_value > 10000:
                size_indicator = "🐟"  # Рыба
            else:
                size_indicator = "🦐"  # Креветка
            
            print(f"\\n🎯 [{time_str}] FUTURES ИСПОЛНЕНИЕ #{self.update_count}")
            print(f"💱 {symbol}")
            print(f"🆔 Trade ID: {trade_id}")
            print(f"📋 Order ID: {order_id[-12:] if len(order_id) > 12 else order_id}")
            print(f"{side_emoji} Сторона: {side_text} │ Тип: {order_type.upper()}")
            print(f"💰 Цена: ${fill_price:,.4f}")
            print(f"📊 Размер: {fill_size:,.0f} контрактов")
            print(f"💵 Стоимость: ${fill_value:,.2f} {size_indicator}")
            print(f"⚡ Плечо: {leverage:.0f}x │ Маржа: {margin_mode}")
            
            # Специальные флаги
            flags = []
            if reduce_only:
                flags.append("🔒 ЗАКРЫТИЕ")
            
            if flags:
                print(f"🏷️ Флаги: {' │ '.join(flags)}")
            
            # Информация о комиссии
            if fee_amount > 0:
                print(f"💸 Комиссия: {fee_amount:,.6f} {fee_coin}")
                if fee_coin == 'USDT':
                    fee_percent = (fee_amount / fill_value) * 100 if fill_value > 0 else 0
                    print(f"📈 % комиссии: {fee_percent:.4f}%")
            
            # Показываем статистику каждые 5 исполнений
            if self.update_count % 5 == 0:
                print("─" * 60)
    
    def update_trading_stats(self, symbol, side, fill_size, fill_price, fee_amount, leverage, reduce_only):
        """Обновить торговую статистику"""
        self.trading_stats['total_fills'] += 1
        self.trading_stats['pairs_traded'].add(symbol)
        
        if side.lower() == 'buy':
            self.trading_stats['long_fills'] += 1
        else:
            self.trading_stats['short_fills'] += 1
        
        if reduce_only:
            self.trading_stats['reduce_only_fills'] += 1
        
        fill_value = fill_price * fill_size
        self.trading_stats['total_volume'] += fill_value
        self.trading_stats['total_fees'] += fee_amount
        
        # Среднее плечо
        current_avg = self.trading_stats['avg_leverage']
        count = self.trading_stats['total_fills']
        self.trading_stats['avg_leverage'] = ((current_avg * (count - 1)) + leverage) / count
    
    def show_trading_summary(self, *args, **kwargs):
        """Метод удален - показываем только оригинальные JSON"""
        pass
    def show_recent_fills(self, *args, **kwargs):
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

async def monitor_all_futures_fills():
    """Мониторинг - показывает оригинальные JSON"""
    config = load_config()
    if not config:
        return
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return
    
    print("🎯 МОНИТОРИНГ ВСЕХ FUTURES ИСПОЛНЕНИЙ")
    print("=" * 40)
    print("🔐 Требуется аутентификация для приватных данных")
    
    fills_client = FuturesFillsChannel(config)
    
    try:
        if not await fills_client.connect():
            return
        
        await fills_client.authenticate()
        
        print("🔄 Мониторинг исполнений фьючерсов...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await fills_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await fills_client.disconnect()

async def leverage_analysis():
    """Упрощенный трекер - показывает только JSON"""
    config = load_config()
    if not config:
        return
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return
    
    print("⚡ АНАЛИЗ ИСПОЛЬЗОВАНИЯ ПЛЕЧА")
    print("=" * 40)
    
    duration = input("⏰ Время анализа в секундах (по умолчанию 300): ").strip()
    try:
        duration = int(duration) if duration else 300
    except ValueError:
        duration = 300
    
    fills_client = FuturesFillsChannel(config)
    
    try:
        if not await fills_client.connect():
            return
        
        await fills_client.authenticate()
        await asyncio.sleep(1)
        await fills_client.subscribe_fills()
        
        print(f"🔄 Анализ плеча в торговле в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(fills_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\\n⏰ Анализ завершен ({duration} сек)")
            
            # Детальный анализ плеча
            if fills_client.fills_data:
                leverages = [fill['leverage'] for fill in fills_client.fills_data.values() if fill['leverage'] > 0]
                
                if leverages:
                    avg_leverage = sum(leverages) / len(leverages)
                    max_leverage = max(leverages)
                    min_leverage = min(leverages)
                    
                    print(f"\\n⚡ РЕЗУЛЬТАТЫ АНАЛИЗА ПЛЕЧА:")
                    print(f"📊 Среднее плечо: {avg_leverage:.2f}x")
                    print(f"📈 Максимальное плечо: {max_leverage:.0f}x")
                    print(f"📉 Минимальное плечо: {min_leverage:.0f}x")
                    
                    # Группы риска
                    conservative = sum(1 for lev in leverages if lev <= 5)
                    moderate = sum(1 for lev in leverages if 5 < lev <= 20)
                    aggressive = sum(1 for lev in leverages if lev > 20)
                    
                    print(f"\\n📊 Распределение торговли:")
                    print(f"🟢 Консервативная (≤5x): {conservative} исполнений")
                    print(f"🟡 Умеренная (5-20x): {moderate} исполнений")
                    print(f"🔴 Агрессивная (>20x): {aggressive} исполнений")
                    
                    # Рекомендации
                    if avg_leverage > 25:
                        print("⚠️ ВЫСОКИЙ РИСК: Очень агрессивное использование плеча!")
                    elif avg_leverage > 15:
                        print("🟡 УМЕРЕННЫЙ РИСК: Повышенное плечо")
                    elif avg_leverage > 10:
                        print("🟠 СРЕДНИЙ РИСК: Сбалансированное плечо")
                    else:
                        print("🟢 НИЗКИЙ РИСК: Консервативное плечо")
                else:
                    print("📭 Данных о плече не найдено")
            else:
                print("📭 Исполнений не зафиксировано")
        
    except KeyboardInterrupt:
        print("\\n👋 Анализ остановлен")
    finally:
        await fills_client.disconnect()

async def trading_session_analytics():
    """Аналитика торговой сессии"""
    config = load_config()
    if not config:
        return
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return
    
    print("📊 АНАЛИТИКА ТОРГОВОЙ СЕССИИ")
    print("=" * 40)
    
    duration = input("⏰ Длительность сессии в секундах (по умолчанию 600): ").strip()
    try:
        duration = int(duration) if duration else 600
    except ValueError:
        duration = 600
    
    fills_client = FuturesFillsChannel(config)
    
    try:
        if not await fills_client.connect():
            return
        
        await fills_client.authenticate()
        await asyncio.sleep(1)
        await fills_client.subscribe_fills()
        
        print(f"🔄 Аналитика торговой сессии в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        start_time = time.time()
        
        try:
            await asyncio.wait_for(fills_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            end_time = time.time()
            session_duration = end_time - start_time
            
            print(f"\\n⏰ Торговая сессия завершена ({session_duration:.0f} сек)")
            print("📊 ДЕТАЛЬНАЯ АНАЛИТИКА:")
            
            stats = fills_client.trading_stats
            
            if stats['total_fills'] > 0:
                # Интенсивность торговли
                fills_per_minute = (stats['total_fills'] / session_duration) * 60
                volume_per_minute = (stats['total_volume'] / session_duration) * 60
                
                print(f"\\n⚡ Интенсивность торговли:")
                print(f"📈 Исполнений в минуту: {fills_per_minute:.2f}")
                print(f"💰 Объем в минуту: ${volume_per_minute:,.2f}")
                
                # Эффективность
                avg_trade_size = stats['total_volume'] / stats['total_fills']
                fee_efficiency = (stats['total_fees'] / stats['total_volume']) * 100
                
                print(f"\\n💎 Эффективность:")
                print(f"📊 Средний размер сделки: ${avg_trade_size:,.2f}")
                print(f"💸 Эффективность комиссий: {fee_efficiency:.4f}%")
                
                # Стратегический анализ
                long_ratio = stats['long_fills'] / stats['total_fills']
                reduce_ratio = stats['reduce_only_fills'] / stats['total_fills']
                
                print(f"\\n📋 Стратегический анализ:")
                print(f"📈 Доля лонгов: {long_ratio:.1%}")
                print(f"📉 Доля шортов: {(1-long_ratio):.1%}")
                print(f"🔒 Доля закрытий: {reduce_ratio:.1%}")
                
                # Оценка сессии
                if fills_per_minute > 2:
                    activity_level = "🔥 ОЧЕНЬ АКТИВНАЯ"
                elif fills_per_minute > 0.5:
                    activity_level = "⚡ АКТИВНАЯ"
                elif fills_per_minute > 0.1:
                    activity_level = "📊 УМЕРЕННАЯ"
                else:
                    activity_level = "😴 СПОКОЙНАЯ"
                
                print(f"\\n🎯 Оценка сессии: {activity_level}")
                
                if stats['avg_leverage'] > 20:
                    risk_assessment = "🔴 ВЫСОКИЙ РИСК"
                elif stats['avg_leverage'] > 10:
                    risk_assessment = "🟡 УМЕРЕННЫЙ РИСК"
                else:
                    risk_assessment = "🟢 НИЗКИЙ РИСК"
                
                print(f"⚠️ Риск-профиль: {risk_assessment}")
            else:
                print("📭 Исполнений не зафиксировано")
        
    except KeyboardInterrupt:
        print("\\n👋 Аналитика остановлена")
    finally:
        await fills_client.disconnect()

async def main():
    """Основная функция"""
    print("🔌 Мониторинг исполнений фьючерсов")
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. 🎯 Все исполнения фьючерсов")
    print("2. ⚡ Анализ использования плеча")
    print("3. 📊 Аналитика торговой сессии")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        if choice == "1":
            await monitor_all_futures_fills()
        elif choice == "2":
            await leverage_analysis()
        elif choice == "3":
            await trading_session_analytics()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")

if __name__ == "__main__":
    asyncio.run(main())
