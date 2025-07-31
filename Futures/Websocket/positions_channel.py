#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures WebSocket - Positions Channel (Private)

Канал для получения данных позиций в реальном времени.
Требует аутентификации для получения приватных данных.

МОДИФИЦИРОВАННАЯ ВЕРСИЯ: Выводит оригинальные JSON сообщения от биржи с отступами.
Больше никакого форматирования - только оригинальные поля биржи.

Документация: https://www.bitget.com/api-doc/contract/websocket/private/Positions-Channel

Структура данных:
- symbol: торговая пара
- size: размер позиции
- side: сторона позиции (long/short)
- markPrice: маркетная цена
- avgPrice: средняя цена входа
- leverage: плечо
- marginMode: режим маржи (crossed/isolated)
- unrealizedPL: нереализованная прибыль/убыток
- percentage: процент прибыли/убытка
- margin: размер маржи
- available: доступно для закрытия
- locked: заблокировано
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

class FuturesPositionsChannel:
    def __init__(self, config):
        self.config = config
        self.ws = None        
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
    
    async def subscribe_positions(self, symbol=None):
        """Подписка на позиции"""
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "instType": "USDT-FUTURES",
                    "channel": "positions",
                    "instId": "default"  # Для всех позиций используется "default"
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
            print("📡 Подписка на все позиции USDT-FUTURES")
    
    def get_position_emoji(self, *args, **kwargs):
        """Метод удален - показываем только оригинальные JSON"""
        pass
    def format_position_data(self, data):
        """Вывод оригинальных JSON данных от биржи"""
        print(json.dumps(data, indent=4, ensure_ascii=False))
    
    def show_portfolio_summary(self, *args, **kwargs):
        """Метод удален - показываем только оригинальные JSON"""
        pass
    def show_pnl_history(self, *args, **kwargs):
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

async def monitor_all_positions():
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
    
    print("🎯 МОНИТОРИНГ ВСЕХ ПОЗИЦИЙ")
    print("=" * 40)
    print("🔐 Требуется аутентификация для приватных данных")
    
    positions_client = FuturesPositionsChannel(config)
    
    try:
        if not await positions_client.connect():
            return
        
        await positions_client.authenticate()
        await positions_client.subscribe_positions()  # Добавляем подписку на позиции!
        
        print("🔄 Мониторинг позиций...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await positions_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await positions_client.disconnect()

async def pnl_tracker():
    """JSON трекер"""
    config = load_config()
    if not config:
        return
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return
    
    print("📈 ТРЕКЕР PNL")
    print("=" * 40)
    
    # Настройки уведомлений
    profit_threshold = input("🟢 Порог прибыли для уведомления в % (по умолчанию 5): ").strip()
    loss_threshold = input("🔴 Порог убытка для уведомления в % (по умолчанию -5): ").strip()
    
    try:
        profit_threshold = float(profit_threshold) if profit_threshold else 5.0
        loss_threshold = float(loss_threshold) if loss_threshold else -5.0
    except ValueError:
        profit_threshold = 5.0
        loss_threshold = -5.0
    
    positions_client = FuturesPositionsChannel(config)
    
    # Переопределяем форматирование для фокуса на PnL
    original_format = positions_client.format_position_data
    
    def pnl_focused_format(data):
        """Форматирование с фокусом на PnL и уведомлениями"""
        original_format(data)
        
        # Проверяем пороги
        for position in data.get('data', []):
            symbol = position.get('symbol', 'N/A')
            percentage = float(position.get('percentage', 0))
            unrealized_pl = float(position.get('unrealizedPL', 0))
            
            if percentage >= profit_threshold:
                print(f"🚨 УВЕДОМЛЕНИЕ: {symbol} достиг порога прибыли {percentage:+.2f}% (${unrealized_pl:+.2f})")
            elif percentage <= loss_threshold:
                print(f"⚠️ ПРЕДУПРЕЖДЕНИЕ: {symbol} достиг порога убытка {percentage:+.2f}% (${unrealized_pl:+.2f})")
    
    positions_client.format_position_data = pnl_focused_format
    
    try:
        if not await positions_client.connect():
            return
        
        await positions_client.authenticate()
        await positions_client.subscribe_positions()  # Добавляем подписку на позиции!
        
        print(f"🔄 Трекер PnL активен...")
        print(f"🟢 Уведомления о прибыли: >= {profit_threshold}%")
        print(f"🔴 Уведомления об убытке: <= {loss_threshold}%")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await positions_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Трекер остановлен")
    finally:
        await positions_client.disconnect()

async def position_risk_monitor():
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
    
    print("⚠️ МОНИТОРИНГ РИСКОВ ПОЗИЦИЙ")
    print("=" * 40)
    
    duration = input("⏰ Время мониторинга в секундах (по умолчанию 600): ").strip()
    try:
        duration = int(duration) if duration else 600
    except ValueError:
        duration = 600
    
    positions_client = FuturesPositionsChannel(config)
    
    try:
        if not await positions_client.connect():
            return
        
        await positions_client.authenticate()
        await positions_client.subscribe_positions()  # Добавляем подписку на позиции!
        
        print(f"🔄 Мониторинг рисков в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(positions_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\n⏰ Мониторинг завершен ({duration} сек)")
        
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен")
    finally:
        await positions_client.disconnect()

async def main():
    """Основная функция"""
    print("🎯 BITGET FUTURES POSITIONS CHANNEL (JSON)")
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. 🎯 Все позиции")
    print("2. 📈 Трекер PnL с уведомлениями")
    print("3. ⚠️ Мониторинг рисков")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        if choice == "1":
            await monitor_all_positions()
        elif choice == "2":
            await pnl_tracker()
        elif choice == "3":
            await position_risk_monitor()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")

if __name__ == "__main__":
    asyncio.run(main())
