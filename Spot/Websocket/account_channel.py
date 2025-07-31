#!/usr/bin/env python3
"""
Bitget Spot WebSocket - Account Channel (Private)

Канал для получения данных баланса аккаунта в реальном времени.
Требует аутентификации для получения приватных данных.

МОДИФИЦИРОВАННАЯ ВЕРСИЯ: Выводит оригинальные JSON сообщения от биржи с отступами.
Больше никакого форматирования - только оригинальные поля биржи.

Документация: https://www.bitget.com/api-doc/spot/websocket/private/Account-Channel

Структура данных:
- coin: валюта
- available: доступный баланс
- frozen: замороженный баланс
- locked: заблокированный баланс
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

class SpotAccountChannel:
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
    
    async def subscribe_account(self):
        """Подписка на изменения баланса аккаунта"""
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "instType": "SPOT",
                    "channel": "account",
                    "instId": "default"
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
            print("📡 Подписка на изменения баланса аккаунта")
    
    def format_balance_data(self, data):
        """Вывод оригинальных JSON данных от биржи"""
        print(json.dumps(data, indent=4, ensure_ascii=False))

    def show_portfolio_summary(self, *args, **kwargs):
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

async def monitor_account_balance():
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
    
    print("💰 МОНИТОРИНГ БАЛАНСА АККАУНТА")
    print("=" * 40)
    print("🔐 Требуется аутентификация для приватных данных")
    
    account_client = SpotAccountChannel(config)
    
    try:
        if not await account_client.connect():
            return
        
        await account_client.authenticate()
        
        print("🔄 Мониторинг изменений баланса...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await account_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await account_client.disconnect()

async def balance_tracker_with_timer():
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
    
    print("⏰ ТРЕКЕР БАЛАНСА С ТАЙМЕРОМ")
    print("=" * 40)
    
    duration = input("⏰ Время мониторинга в секундах (по умолчанию 300): ").strip()
    try:
        duration = int(duration) if duration else 300
    except ValueError:
        duration = 300
    
    account_client = SpotAccountChannel(config)
    
    try:
        if not await account_client.connect():
            return
        
        await account_client.authenticate()
        
        print(f"🔄 Мониторинг баланса в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(account_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\\n⏰ Время мониторинга ({duration} сек) истекло")
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await account_client.disconnect()

async def main():
    """Основная функция"""
    print("💰 BITGET SPOT ACCOUNT CHANNEL (JSON)")
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. 💰 Непрерывный мониторинг баланса")
    print("2. ⏰ Мониторинг с таймером")
    
    try:
        choice = input("Ваш выбор (1-2): ").strip()
        
        if choice == "1":
            await monitor_account_balance()
        elif choice == "2":
            await balance_tracker_with_timer()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")

if __name__ == "__main__":
    asyncio.run(main())
