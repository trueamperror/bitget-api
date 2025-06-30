#!/usr/bin/env python3
"""
Bitget Spot WebSocket - Orders Channel (Private)

Канал для получения обновлений по ордерам в реальном времени.
Требует аутентификации для получения приватных данных.

Документация: https://www.bitget.com/api-doc/spot/websocket/private/Orders-Channel

Структура данных:
- orderId: ID ордера
- clientOid: клиентский ID ордера  
- instId: торговая пара
- side: сторона (buy/sell)
- orderType: тип ордера (limit/market)
- size: размер ордера
- price: цена ордера
- status: статус ордера
- fillPrice: цена исполнения
- fillSize: размер исполнения
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


class SpotOrdersChannel:
    def __init__(self, config):
        self.config = config
        self.ws = None
        self.orders_data = {}
        self.update_count = 0
        self.order_stats = {
            'new': 0,
            'filled': 0,
            'cancelled': 0,
            'partially_filled': 0
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
    
    async def subscribe_orders(self, symbol=None):
        """Подписка на обновления ордеров"""
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "instType": "SPOT",
                    "channel": "orders",
                    "instId": symbol if symbol else "default"
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
            if symbol:
                print(f"📡 Подписка на ордера для {symbol}")
            else:
                print("📡 Подписка на все ордера")
    
    def get_status_emoji(self, status):
        """Получить эмодзи для статуса ордера"""
        status_emojis = {
            'new': '🆕',
            'partial_fill': '🔄',
            'full_fill': '✅',
            'cancelled': '❌',
            'live': '🟢',
            'partially_filled': '🔄',
            'filled': '✅',
            'canceled': '❌'
        }
        return status_emojis.get(status.lower(), '❓')
    
    def get_side_emoji(self, side):
        """Получить эмодзи для стороны ордера"""
        return "🟢" if side == "buy" else "🔴"
    
    def format_order_data(self, data):
        """Форматирование данных ордеров"""
        if not data or 'data' not in data:
            return
        
        for order_update in data['data']:
            self.update_count += 1
            
            order_id = order_update.get('orderId', 'N/A')
            client_oid = order_update.get('clientOid', 'N/A')
            inst_id = order_update.get('instId', 'N/A')
            side = order_update.get('side', 'N/A')
            order_type = order_update.get('orderType', 'N/A')
            size = float(order_update.get('size', 0))
            price = float(order_update.get('price', 0))
            status = order_update.get('status', 'N/A')
            fill_price = float(order_update.get('fillPrice', 0))
            fill_size = float(order_update.get('fillSize', 0))
            fill_time = order_update.get('fillTime', 0)
            create_time = order_update.get('cTime', 0)
            update_time = order_update.get('uTime', 0)
            
            # Обновляем данные ордера
            self.orders_data[order_id] = {
                'clientOid': client_oid,
                'instId': inst_id,
                'side': side,
                'orderType': order_type,
                'size': size,
                'price': price,
                'status': status,
                'fillPrice': fill_price,
                'fillSize': fill_size,
                'fillTime': fill_time,
                'createTime': create_time,
                'updateTime': update_time,
                'last_update': datetime.now()
            }
            
            # Обновляем статистику
            self.update_order_stats(status)
            
            # Форматирование времени
            if update_time:
                dt = datetime.fromtimestamp(int(update_time) / 1000)
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Получаем эмодзи
            status_emoji = self.get_status_emoji(status)
            side_emoji = self.get_side_emoji(side)
            
            print(f"\\n📋 [{time_str}] ОРДЕР #{self.update_count}")
            print(f"💱 {inst_id}")
            print(f"🆔 Order ID: {order_id}")
            if client_oid != 'N/A':
                print(f"👤 Client ID: {client_oid}")
            print(f"{side_emoji} Сторона: {side.upper()} │ Тип: {order_type.upper()}")
            print(f"{status_emoji} Статус: {status.upper()}")
            print(f"📊 Размер: {size:,.6f}")
            if price > 0:
                print(f"💰 Цена: ${price:,.6f}")
            
            # Информация об исполнении
            if fill_size > 0:
                fill_percent = (fill_size / size) * 100 if size > 0 else 0
                print(f"✅ Исполнено: {fill_size:,.6f} ({fill_percent:.2f}%)")
                if fill_price > 0:
                    print(f"💵 Цена исполнения: ${fill_price:,.6f}")
                    print(f"💸 Сумма исполнения: ${fill_price * fill_size:,.2f}")
            
            # Показываем статистику каждые 10 обновлений
            if self.update_count % 10 == 0:
                self.show_orders_summary()
            
            print("─" * 50)
    
    def update_order_stats(self, status):
        """Обновить статистику ордеров"""
        status_lower = status.lower()
        if status_lower in ['new', 'live']:
            self.order_stats['new'] += 1
        elif status_lower in ['filled', 'full_fill']:
            self.order_stats['filled'] += 1
        elif status_lower in ['cancelled', 'canceled']:
            self.order_stats['cancelled'] += 1
        elif status_lower in ['partial_fill', 'partially_filled']:
            self.order_stats['partially_filled'] += 1
    
    def show_orders_summary(self):
        """Показать сводку по ордерам"""
        if not self.orders_data:
            return
        
        print(f"\\n📊 СВОДКА ОРДЕРОВ (обновлено: {datetime.now().strftime('%H:%M:%S')})")
        print("=" * 60)
        
        print(f"📋 Всего ордеров: {len(self.orders_data)}")
        print(f"🔄 Всего обновлений: {self.update_count}")
        
        # Статистика по статусам
        print(f"\\n📈 Статистика по статусам:")
        print(f"🆕 Новые: {self.order_stats['new']}")
        print(f"✅ Исполненные: {self.order_stats['filled']}")
        print(f"❌ Отмененные: {self.order_stats['cancelled']}")
        print(f"🔄 Частично исполненные: {self.order_stats['partially_filled']}")
        
        # Группировка по парам
        pairs_count = {}
        for order_data in self.orders_data.values():
            pair = order_data['instId']
            pairs_count[pair] = pairs_count.get(pair, 0) + 1
        
        if pairs_count:
            print(f"\\n💱 Торговые пары:")
            for pair, count in sorted(pairs_count.items(), key=lambda x: x[1], reverse=True):
                print(f"  {pair}: {count} ордеров")
        
        # Последние ордера
        recent_orders = sorted(
            self.orders_data.items(),
            key=lambda x: x[1]['last_update'],
            reverse=True
        )[:5]
        
        if recent_orders:
            print(f"\\n🕐 Последние 5 ордеров:")
            print(f"{'ID':^15} {'Пара':^12} {'Сторона':^8} {'Статус':^15} {'Размер':>12}")
            print("─" * 70)
            
            for order_id, data in recent_orders:
                short_id = order_id[-8:] if len(order_id) > 8 else order_id
                status_emoji = self.get_status_emoji(data['status'])
                side_emoji = self.get_side_emoji(data['side'])
                
                print(f"{short_id:^15} {data['instId']:^12} {side_emoji}{data['side'][:3]:^7} {status_emoji}{data['status'][:12]:^14} {data['size']:>12.4f}")
    
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
            
            # Обработка данных ордеров
            elif data.get('action') in ['snapshot', 'update']:
                channel = data.get('arg', {}).get('channel', '')
                if channel == 'orders':
                    self.format_order_data(data)
            
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
            self.show_orders_summary()


async def monitor_all_orders():
    """Мониторинг всех ордеров"""
    config = load_config()
    if not config:
        return
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return
    
    print("📋 МОНИТОРИНГ ВСЕХ ОРДЕРОВ")
    print("=" * 40)
    print("🔐 Требуется аутентификация для приватных данных")
    
    orders_client = SpotOrdersChannel(config)
    
    try:
        if not await orders_client.connect():
            return
        
        # Ждем успешной аутентификации
        if not await orders_client.authenticate():
            print("❌ Не удалось аутентифицироваться")
            return
        
        # Небольшая пауза после аутентификации
        await asyncio.sleep(1)
        
        # Подписываемся на ордера
        await orders_client.subscribe_orders()
        
        print("🔄 Мониторинг обновлений ордеров...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await orders_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await orders_client.disconnect()


async def monitor_pair_orders():
    """Мониторинг ордеров конкретной пары"""
    config = load_config()
    if not config:
        return
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return
    
    print("📋 МОНИТОРИНГ ОРДЕРОВ КОНКРЕТНОЙ ПАРЫ")
    print("=" * 40)
    
    symbol = input("💱 Введите торговую пару (например, BTCUSDT) или оставьте пустым для всех: ").strip().upper()
    
    orders_client = SpotOrdersChannel(config)
    
    try:
        if not await orders_client.connect():
            return
        
        # Ждем успешной аутентификации
        if not await orders_client.authenticate():
            print("❌ Не удалось аутентифицироваться")
            return
        
        # Небольшая задержка для аутентификации
        await asyncio.sleep(1)
        
        if symbol:
            await orders_client.subscribe_orders(symbol)
            print(f"🔄 Мониторинг ордеров для {symbol}...")
        else:
            await orders_client.subscribe_orders()
            print("🔄 Мониторинг всех ордеров...")
        
        print("💡 Нажмите Ctrl+C для остановки")
        
        await orders_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await orders_client.disconnect()


async def orders_tracker_with_timer():
    """Трекер ордеров с таймером"""
    config = load_config()
    if not config:
        return
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return
    
    print("⏰ ТРЕКЕР ОРДЕРОВ С ТАЙМЕРОМ")
    print("=" * 40)
    
    duration = input("⏰ Время мониторинга в секундах (по умолчанию 300): ").strip()
    try:
        duration = int(duration) if duration else 300
    except ValueError:
        duration = 300
    
    orders_client = SpotOrdersChannel(config)
    
    try:
        if not await orders_client.connect():
            return
        
        # Ждем успешной аутентификации
        if not await orders_client.authenticate():
            print("❌ Не удалось аутентифицироваться")
            return
            
        await asyncio.sleep(1)
        await orders_client.subscribe_orders()
        
        print(f"🔄 Мониторинг ордеров в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(orders_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\\n⏰ Время мониторинга ({duration} сек) истекло")
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await orders_client.disconnect()


async def main():
    """Основная функция"""
    print("📋 BITGET SPOT ORDERS CHANNEL")
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. 📋 Все ордера")
    print("2. 💱 Ордера конкретной пары")
    print("3. ⏰ Мониторинг с таймером")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        if choice == "1":
            await monitor_all_orders()
        elif choice == "2":
            await monitor_pair_orders()
        elif choice == "3":
            await orders_tracker_with_timer()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")


if __name__ == "__main__":
    asyncio.run(main())
