#!/usr/bin/env python3
"""
Bitget Spot WebSocket - Fills Channel (Private)

Канал для получения данных об исполненных сделках в реальном времени.
Требует аутентификации для получения приватных данных.

МОДИФИЦИРОВАННАЯ ВЕРСИЯ: Выводит оригинальные JSON сообщения от биржи с отступами.
Больше никакого форматирования - только оригинальные поля биржи.

Документация: https://www.bitget.com/api-doc/spot/websocket/private/Fills-Channel

Структура данных:
- tradeId: ID сделки
- orderId: ID ордера
- instId: торговая пара
- side: сторона (buy/sell)
- fillSize: размер исполнения
- fillPrice: цена исполнения
- orderType: тип ордера
- feeAmount: размер комиссии
- feeCoin: валюта комиссии
- fillTime: время исполнения
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

class SpotFillsChannel:
    def __init__(self, config):
        self.config = config
        self.ws = None
        self.fills_data = {}
        self.update_count = 0
        self.trading_stats = {
            'total_fills': 0,
            'buy_fills': 0,
            'sell_fills': 0,
            'total_volume': 0,
            'total_fees': 0,
            'pairs_traded': set()
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
            
            # Используем приватный WebSocket URL
            private_ws_url = self.config.get('privateWsURL', 'wss://ws.bitget.com/v2/ws/private')
            
            self.ws = await websockets.connect(
                private_ws_url,
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10
            )
            print("✅ Подключение к Private Spot WebSocket установлено")
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
        """Подписка на исполнения"""
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "instType": "SPOT",
                    "channel": "fills",
                    "instId": symbol if symbol else "default"
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
            if symbol:
                print(f"📡 Подписка на исполнения для {symbol}")
            else:
                print("📡 Подписка на все исполнения")
    
    def format_fill_data(self, data):
        """Форматирование данных исполнений"""
        if not data or 'data' not in data:
            return
        
        for fill in data['data']:
            self.update_count += 1
            
            trade_id = fill.get('tradeId', 'N/A')
            order_id = fill.get('orderId', 'N/A')
            inst_id = fill.get('instId', 'N/A')
            side = fill.get('side', 'N/A')
            fill_size = float(fill.get('fillSize', 0))
            fill_price = float(fill.get('fillPrice', 0))
            order_type = fill.get('orderType', 'N/A')
            fee_amount = float(fill.get('feeAmount', 0))
            fee_coin = fill.get('feeCoin', 'N/A')
            fill_time = fill.get('fillTime', 0)
            
            # Обновляем статистику
            self.update_trading_stats(inst_id, side, fill_size, fill_price, fee_amount)
            
            # Сохраняем данные исполнения
            self.fills_data[trade_id] = {
                'orderId': order_id,
                'instId': inst_id,
                'side': side,
                'fillSize': fill_size,
                'fillPrice': fill_price,
                'orderType': order_type,
                'feeAmount': fee_amount,
                'feeCoin': fee_coin,
                'fillTime': fill_time,
                'timestamp': datetime.now()
            }
            
            # Форматирование времени
            if fill_time:
                dt = datetime.fromtimestamp(int(fill_time) / 1000)
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Эмодзи для стороны сделки
            side_emoji = "🟢" if side == "buy" else "🔴"
            side_arrow = "⬆️" if side == "buy" else "⬇️"
            
            # Расчет суммы исполнения
            fill_value = fill_price * fill_size
            
            print(f"\\n🎯 [{time_str}] ИСПОЛНЕНИЕ #{self.update_count}")
            print(f"💱 {inst_id}")
            print(f"🆔 Trade ID: {trade_id}")
            print(f"📋 Order ID: {order_id[-12:] if len(order_id) > 12 else order_id}")
            print(f"{side_arrow} Сторона: {side_emoji} {side.upper()} │ Тип: {order_type.upper()}")
            print(f"💰 Цена: ${fill_price:,.6f}")
            print(f"📊 Размер: {fill_size:,.6f}")
            print(f"💵 Сумма: ${fill_value:,.2f}")
            
            # Информация о комиссии
            if fee_amount > 0:
                print(f"💸 Комиссия: {fee_amount:,.6f} {fee_coin}")
                if fee_coin == 'USDT':
                    fee_percent = (fee_amount / fill_value) * 100 if fill_value > 0 else 0
                    print(f"📈 Комиссия: {fee_percent:.4f}%")
            
            # Показываем статистику каждые 5 исполнений
            if self.update_count % 5 == 0:
                print("─" * 50)
    
    def update_trading_stats(self, inst_id, side, fill_size, fill_price, fee_amount):
        """Обновить торговую статистику"""
        self.trading_stats['total_fills'] += 1
        self.trading_stats['pairs_traded'].add(inst_id)
        
        if side == 'buy':
            self.trading_stats['buy_fills'] += 1
        else:
            self.trading_stats['sell_fills'] += 1
        
        fill_value = fill_price * fill_size
        self.trading_stats['total_volume'] += fill_value
        self.trading_stats['total_fees'] += fee_amount
    
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

async def monitor_all_fills():
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
    
    print("🎯 МОНИТОРИНГ ВСЕХ ИСПОЛНЕНИЙ")
    print("=" * 40)
    print("🔐 Требуется аутентификация для приватных данных")
    
    fills_client = SpotFillsChannel(config)
    
    try:
        if not await fills_client.connect():
            return
        
        # Ждем успешной аутентификации
        if not await fills_client.authenticate():
            print("❌ Не удалось аутентифицироваться")
            return
        
        # Небольшая пауза после аутентификации
        await asyncio.sleep(1)
        
        # Подписываемся на исполнения
        await fills_client.subscribe_fills()
        
        print("🔄 Мониторинг исполнений...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await fills_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await fills_client.disconnect()

async def monitor_pair_fills():
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
    
    print("🎯 МОНИТОРИНГ ИСПОЛНЕНИЙ КОНКРЕТНОЙ ПАРЫ")
    print("=" * 40)
    
    symbol = input("💱 Введите торговую пару (например, BTCUSDT) или оставьте пустым для всех: ").strip().upper()
    
    fills_client = SpotFillsChannel(config)
    
    try:
        if not await fills_client.connect():
            return
        
        # Ждем успешной аутентификации
        if not await fills_client.authenticate():
            print("❌ Не удалось аутентифицироваться")
            return
        
        # Небольшая задержка для аутентификации
        await asyncio.sleep(1)
        
        if symbol:
            await fills_client.subscribe_fills(symbol)
            print(f"🔄 Мониторинг исполнений для {symbol}...")
        else:
            await fills_client.subscribe_fills()
            print("🔄 Мониторинг всех исполнений...")
        
        print("💡 Нажмите Ctrl+C для остановки")
        
        await fills_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await fills_client.disconnect()

async def trading_session_analysis():
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
    
    print("📊 АНАЛИЗ ТОРГОВОЙ СЕССИИ")
    print("=" * 40)
    
    duration = input("⏰ Длительность сессии в секундах (по умолчанию 600): ").strip()
    try:
        duration = int(duration) if duration else 600
    except ValueError:
        duration = 600
    
    fills_client = SpotFillsChannel(config)
    
    try:
        if not await fills_client.connect():
            return
        
        # Ждем успешной аутентификации
        if not await fills_client.authenticate():
            print("❌ Не удалось аутентифицироваться")
            return
            
        await asyncio.sleep(1)
        await fills_client.subscribe_fills()
        
        print(f"🔄 Анализ торговой сессии в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        start_time = time.time()
        
        try:
            await asyncio.wait_for(fills_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            end_time = time.time()
            session_duration = end_time - start_time
            
            print(f"\\n⏰ Торговая сессия завершена ({session_duration:.0f} сек)")
            print("📊 ФИНАЛЬНЫЙ АНАЛИЗ:")
            
            # Детальная статистика
            stats = fills_client.trading_stats
            if stats['total_fills'] > 0:
                avg_fills_per_minute = (stats['total_fills'] / session_duration) * 60
                print(f"⚡ Скорость торговли: {avg_fills_per_minute:.2f} исполнений/мин")
                
                if stats['total_volume'] > 0:
                    avg_volume_per_minute = (stats['total_volume'] / session_duration) * 60
                    print(f"💰 Объем в минуту: ${avg_volume_per_minute:,.2f}")
            else:
                print("📭 Исполнений не зафиксировано")
        
    except KeyboardInterrupt:
        print("\\n👋 Анализ остановлен")
    finally:
        await fills_client.disconnect()

async def main():
    """Основная функция"""
    print("🔌 Мониторинг спот исполнений")
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. 🎯 Все исполнения")
    print("2. 💱 Исполнения конкретной пары")
    print("3. 📊 Анализ торговой сессии")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        if choice == "1":
            await monitor_all_fills()
        elif choice == "2":
            await monitor_pair_fills()
        elif choice == "3":
            await trading_session_analysis()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")

if __name__ == "__main__":
    asyncio.run(main())
