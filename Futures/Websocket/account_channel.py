#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures WebSocket - Account Channel (Private)

Канал для получения обновлений по аккаунту фьючерсов в реальном времени.
Требует аутентификации для получения приватных данных.

МОДИФИЦИРОВАННАЯ ВЕРСИЯ: Выводит оригинальные JSON сообщения от биржи с отступами.
Больше никакого форматирования - только оригинальные поля биржи.

Документация: https://www.bitget.com/api-doc/contract/websocket/private/Account-Channel

Структура данных:
- marginCoin: валюта маржи
- available: доступный баланс
- locked: заблокированный баланс
- total: общий баланс
- unrealizedPL: нереализованная прибыль/убыток
- crossMarginLeverage: плечо кросс-маржи
- isolatedMarginLeverage: плечо изолированной маржи
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

class FuturesAccountChannel:
    def __init__(self, config):
        self.config = config
        self.ws = None
        self.account_data = {}
        self.update_count = 0
        
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
    
    async def subscribe_account(self):
        """Подписка на обновления аккаунта"""
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "instType": "USDT-FUTURES",
                    "channel": "balance"
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
            print(f"📡 Отправлена подписка на аккаунт: {json.dumps(subscribe_message, indent=2)}")
            print("📡 Подписка на данные аккаунта фьючерсов")
            
            # Ждем подтверждение подписки
            try:
                response = await asyncio.wait_for(self.ws.recv(), timeout=5)
                data = json.loads(response)
                print(f"📡 Ответ подписки: {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                print("⚠️ Таймаут ответа подписки")
            except Exception as e:
                print(f"⚠️ Ошибка получения ответа подписки: {e}")
    
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

async def monitor_all_futures_account():
    """Мониторинг аккаунта - показывает оригинальные JSON"""
    config = load_config()
    if not config:
        return
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return
    
    print("📋 МОНИТОРИНГ АККАУНТА FUTURES")
    print("=" * 40)
    print("🔐 Требуется аутентификация для приватных данных")
    
    account_client = FuturesAccountChannel(config)
    
    try:
        if not await account_client.connect():
            return
        
        if not await account_client.authenticate():
            print("❌ Ошибка аутентификации. Проверьте API ключи.")
            return
        
        await asyncio.sleep(1)  # Пауза между аутентификацией и подпиской
        await account_client.subscribe_account()  # Подписываемся на аккаунт
        
        print("🔄 Мониторинг аккаунта фьючерсов...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await account_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await account_client.disconnect()

async def main():
    """Основная функция"""
    print("🔌 Мониторинг аккаунта фьючерсов")
    print("=" * 40)
    
    # Запускаем прямо мониторинг аккаунта
    await monitor_all_futures_account()

if __name__ == "__main__":
    asyncio.run(main())
