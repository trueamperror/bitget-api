#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures WebSocket - Orders Channel (Private)

Канал для получения обновлений по ордерам фьючерсов в реальном времени.
Требует аутентификации для получения приватных данных.

МОДИФИЦИРОВАННАЯ ВЕРСИЯ: Выводит оригинальные JSON сообщения от биржи с отступами.
Больше никакого форматирования - только оригинальные поля биржи.

Документация: https://www.bitget.com/api-doc/contract/websocket/private/Orders-Channel

Структура данных:
- orderId: ID ордера
- clientOid: клиентский ID ордера
- symbol: торговая пара
- side: сторона (buy/sell)
- orderType: тип ордера (limit/market)
- size: размер ордера
- price: цена ордера
- status: статус ордера
- leverage: плечо
- marginMode: режим маржи
- reduceOnly: только закрытие позиции
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

class FuturesOrdersChannel:
    def __init__(self, config):
        self.config = config
        self.ws = None
        self.orders_data = {}
        self.update_count = 0
        self.order_stats = {
            'new': 0,
            'filled': 0,
            'cancelled': 0,
            'partially_filled': 0,
            'total_volume': 0,
            'avg_leverage': 0
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
                print(f"🔐 Ответ аутентификации: {json.dumps(data, indent=2)}")
                
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
                    "instType": "USDT-FUTURES",
                    "channel": "orders",
                    "instId": symbol if symbol else "default"
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
            print(f"📡 Отправлена подписка на ордера: {json.dumps(subscribe_message, indent=2)}")
            if symbol:
                print(f"📡 Подписка на ордера фьючерса {symbol}")
            else:
                print("📡 Подписка на все ордера фьючерсов")
            
            # Ждем подтверждение подписки
            try:
                response = await asyncio.wait_for(self.ws.recv(), timeout=5)
                data = json.loads(response)
                print(f"📡 Ответ подписки: {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                print("⚠️ Таймаут ответа подписки")
            except Exception as e:
                print(f"⚠️ Ошибка получения ответа подписки: {e}")
    
    def get_status_emoji(self, *args, **kwargs):
        """Метод удален - показываем только оригинальные JSON"""
        pass
    def get_side_emoji(self, *args, **kwargs):
        """Метод удален - показываем только оригинальные JSON"""
        pass
    def format_order_data(self, data):
        """Форматирование данных ордеров"""
        if not data or 'data' not in data:
            return
        
        for order_update in data['data']:
            self.update_count += 1
            
            order_id = order_update.get('orderId', 'N/A')
            client_oid = order_update.get('clientOid', 'N/A')
            symbol = order_update.get('symbol', 'N/A')
            side = order_update.get('side', 'N/A')
            order_type = order_update.get('orderType', 'N/A')
            size = float(order_update.get('size', 0))
            price = float(order_update.get('price', 0))
            status = order_update.get('status', 'N/A')
            leverage = float(order_update.get('leverage', 0))
            margin_mode = order_update.get('marginMode', 'N/A')
            reduce_only = order_update.get('reduceOnly', False)
            fill_price = float(order_update.get('fillPrice', 0))
            fill_size = float(order_update.get('fillSize', 0))
            fill_time = order_update.get('fillTime', 0)
            create_time = order_update.get('cTime', 0)
            update_time = order_update.get('uTime', 0)
            
            # Обновляем данные ордера
            self.orders_data[order_id] = {
                'clientOid': client_oid,
                'symbol': symbol,
                'side': side,
                'orderType': order_type,
                'size': size,
                'price': price,
                'status': status,
                'leverage': leverage,
                'marginMode': margin_mode,
                'reduceOnly': reduce_only,
                'fillPrice': fill_price,
                'fillSize': fill_size,
                'fillTime': fill_time,
                'createTime': create_time,
                'updateTime': update_time,
                'last_update': datetime.now()
            }
            
            # Обновляем статистику
            self.update_order_stats(status, size, price, leverage)
            
            # Форматирование времени
            if update_time:
                dt = datetime.fromtimestamp(int(update_time) / 1000)
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Получаем эмодзи
            status_emoji = self.get_status_emoji(status)
            side_emoji = self.get_side_emoji(side)
            
            # Расчет стоимости
            order_value = price * size if price > 0 else 0
            
            print(f"\\n📋 [{time_str}] FUTURES ОРДЕР #{self.update_count}")
            print(f"💱 {symbol}")
            print(f"🆔 Order ID: {order_id[-12:] if len(order_id) > 12 else order_id}")
            if client_oid != 'N/A':
                print(f"👤 Client ID: {client_oid}")
            print(f"{side_emoji} Сторона: {side.upper()} │ Тип: {order_type.upper()}")
            print(f"{status_emoji} Статус: {status.upper()}")
            print(f"📊 Размер: {size:,.0f} контрактов")
            if price > 0:
                print(f"💰 Цена: ${price:,.4f}")
                print(f"💵 Стоимость: ${order_value:,.2f}")
            print(f"⚡ Плечо: {leverage:.0f}x │ Маржа: {margin_mode}")
            
            # Специальные флаги
            flags = []
            if reduce_only:
                flags.append("🔒 ТОЛЬКО ЗАКРЫТИЕ")
            
            if flags:
                print(f"🏷️ Флаги: {' │ '.join(flags)}")
            
            # Информация об исполнении
            if fill_size > 0:
                fill_percent = (fill_size / size) * 100 if size > 0 else 0
                fill_value = fill_price * fill_size if fill_price > 0 else 0
                
                print(f"✅ Исполнено: {fill_size:,.0f} ({fill_percent:.2f}%)")
                if fill_price > 0:
                    print(f"💵 Цена исполнения: ${fill_price:,.4f}")
                    print(f"💸 Сумма исполнения: ${fill_value:,.2f}")
            
            # Показываем статистику каждые 8 обновлений
            if self.update_count % 8 == 0:
                print("─" * 60)
    
    def update_order_stats(self, status, size, price, leverage):
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
        
        # Обновляем объем и среднее плечо
        if price > 0 and size > 0:
            order_value = price * size
            self.order_stats['total_volume'] += order_value
        
        if leverage > 0:
            current_avg = self.order_stats['avg_leverage']
            count = self.update_count
            self.order_stats['avg_leverage'] = ((current_avg * (count - 1)) + leverage) / count
    
    def show_orders_summary(self, *args, **kwargs):
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

async def monitor_all_futures_orders():
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
    
    print("📋 МОНИТОРИНГ ВСЕХ FUTURES ОРДЕРОВ")
    print("=" * 40)
    print("🔐 Требуется аутентификация для приватных данных")
    
    orders_client = FuturesOrdersChannel(config)
    
    try:
        if not await orders_client.connect():
            return
        
        if not await orders_client.authenticate():
            print("❌ Ошибка аутентификации. Проверьте API ключи.")
            return
        
        await asyncio.sleep(1)  # Пауза между аутентификацией и подпиской
        await orders_client.subscribe_orders()  # Добавили подписку!
        
        print("🔄 Мониторинг ордеров фьючерсов...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await orders_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await orders_client.disconnect()

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
    
    orders_client = FuturesOrdersChannel(config)
    
    try:
        if not await orders_client.connect():
            return
        
        await orders_client.authenticate()
        await asyncio.sleep(1)
        await orders_client.subscribe_orders()
        
        print(f"🔄 Анализ плеча в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(orders_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\\n⏰ Анализ завершен ({duration} сек)")
            
            # Детальный анализ плеча
            if orders_client.orders_data:
                leverages = [order['leverage'] for order in orders_client.orders_data.values() if order['leverage'] > 0]
                
                if leverages:
                    avg_leverage = sum(leverages) / len(leverages)
                    max_leverage = max(leverages)
                    min_leverage = min(leverages)
                    
                    print(f"\\n⚡ РЕЗУЛЬТАТЫ АНАЛИЗА ПЛЕЧА:")
                    print(f"📊 Среднее плечо: {avg_leverage:.2f}x")
                    print(f"📈 Максимальное плечо: {max_leverage:.0f}x")
                    print(f"📉 Минимальное плечо: {min_leverage:.0f}x")
                    
                    # Группы риска
                    low_risk = sum(1 for lev in leverages if lev <= 5)
                    medium_risk = sum(1 for lev in leverages if 5 < lev <= 20)
                    high_risk = sum(1 for lev in leverages if lev > 20)
                    
                    print(f"\\n📊 Распределение по риску:")
                    print(f"🟢 Низкий риск (≤5x): {low_risk} ордеров")
                    print(f"🟡 Средний риск (5-20x): {medium_risk} ордеров")
                    print(f"🔴 Высокий риск (>20x): {high_risk} ордеров")
                    
                    if avg_leverage > 20:
                        print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Высокое среднее плечо!")
                    elif avg_leverage > 10:
                        print("🟡 ВНИМАНИЕ: Умеренно высокое плечо")
                    else:
                        print("🟢 Консервативное использование плеча")
                else:
                    print("📭 Данных о плече не найдено")
            else:
                print("📭 Ордеров не зафиксировано")
        
    except KeyboardInterrupt:
        print("\\n👋 Анализ остановлен")
    finally:
        await orders_client.disconnect()

async def order_execution_monitor():
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
    
    print("✅ МОНИТОРИНГ ИСПОЛНЕНИЯ ОРДЕРОВ")
    print("=" * 40)
    
    orders_client = FuturesOrdersChannel(config)
    
    # Переопределяем форматирование для фокуса на исполнении
    original_format = orders_client.format_order_data
    
    def execution_focused_format(data):
        """Форматирование с фокусом на исполнение ордеров"""
        if not data or 'data' not in data:
            return
        
        for order_update in data['data']:
            status = order_update.get('status', 'N/A')
            fill_size = float(order_update.get('fillSize', 0))
            
            # Показываем только ордера с исполнением или изменением статуса
            if status.lower() in ['filled', 'full_fill', 'partially_filled', 'partial_fill'] or fill_size > 0:
                original_format(data)
                break
    
    orders_client.format_order_data = execution_focused_format
    
    try:
        if not await orders_client.connect():
            return
        
        await orders_client.authenticate()
        await asyncio.sleep(1)
        await orders_client.subscribe_orders()
        
        print("🔄 Мониторинг исполнения ордеров...")
        print("💡 Показываются только исполненные ордера")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await orders_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await orders_client.disconnect()

async def main():
    """Основная функция"""
    print("🔌 Мониторинг ордеров фьючерсов")
    print("=" * 40)
    
    # Запускаем прямо мониторинг всех ордеров
    await monitor_all_futures_orders()

if __name__ == "__main__":
    asyncio.run(main())
