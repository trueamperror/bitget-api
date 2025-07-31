#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures WebSocket - Account Channel (Private)

Канал для получения данных баланса фьючерсного аккаунта в реальном времени.
Требует аутентификации для получения приватных данных.

МОДИФИЦИРОВАННАЯ ВЕРСИЯ: Выводит оригинальные JSON сообщения от биржи с отступами.
Больше никакого форматирования - только оригинальные поля биржи.

Документация: https://www.bitget.com/api-doc/contract/websocket/private/Account-Channel
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
        
    def generate_signature(self, timestamp, method, request_path, body=''):
        """Генерация подписи для аутентификации согласно документации Bitget"""
        # Для WebSocket аутентификации используется специальный формат
        message = f"{timestamp}{method}{request_path}{body}"
        
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
            
            # Используем специальный URL для приватных фьючерсных данных
            private_futures_ws_url = 'wss://ws.bitget.com/v2/ws/private'
            
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
    
    async def subscribe_account(self):
        """Подписка на изменения баланса фьючерсного аккаунта"""
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "instType": "USDT-FUTURES",
                    "channel": "account",
                    "coin": "default"  # Согласно документации, используется "coin" а не "instId"
                }
            ]
        }
        
        if self.ws:
            print(f"📡 Подписка на аккаунт: {subscribe_message}")
            await self.ws.send(json.dumps(subscribe_message))
            
            # Ждем подтверждения подписки
            try:
                response = await asyncio.wait_for(self.ws.recv(), timeout=5)
                data = json.loads(response)
                
                if data.get('event') == 'subscribe':
                    # Проверяем успешность подписки
                    if 'code' in data:
                        if str(data.get('code')) == '0':
                            print("✅ Подписка на аккаунт подтверждена")
                            return True
                        else:
                            print(f"❌ Ошибка подписки: {data.get('msg', 'Unknown error')}")
                            print(f"❌ Debug: Полный ответ: {data}")
                            return False
                    else:
                        # Если нет поля code, но есть arg - значит подписка успешна
                        if 'arg' in data:
                            print("✅ Подписка на аккаунт подтверждена (без code)")
                            return True
                        else:
                            print(f"🤔 Неожиданный формат ответа подписки: {data}")
                            return False
                elif data.get('action') == 'snapshot':
                    # Возможно, сразу пришли данные аккаунта
                    print("📊 Получены начальные данные аккаунта")
                    await self.handle_message(json.dumps(data))
                    return True
                else:
                    print(f"🤔 Неожиданный ответ: {data}")
                    return False
                    
            except asyncio.TimeoutError:
                print("⏰ Таймаут подтверждения подписки")
                return False
            except Exception as e:
                print(f"❌ Ошибка при подтверждении подписки: {e}")
                return False
        
        return False
    
    def format_account_data(self, data):
        """Вывод оригинальных JSON данных от биржи"""
        print(json.dumps(data, indent=4, ensure_ascii=False))
    
    def show_account_analytics(self, *args, **kwargs):
        """Метод удален - показываем только оригинальные JSON"""
        pass
    async def handle_message(self, message):
        """Обработка входящих сообщений - вывод оригинальных JSON"""
        try:
            data = json.loads(message)
            print(json.dumps(data, indent=4, ensure_ascii=False))
            
            # Обработка данных аккаунта для вызова format_account_data
            if data.get('action') in ['snapshot', 'update']:
                channel = data.get('arg', {}).get('channel', '')
                if channel == 'account':
                    self.format_account_data(data)
            
            # Пинг-понг
            elif 'ping' in data:
                pong_message = {'pong': data['ping']}
                if self.ws:
                    await self.ws.send(json.dumps(pong_message))
        
        except json.JSONDecodeError:
            print(f"❌ Ошибка декодирования JSON: {message}")
        except Exception as e:
            print(f"❌ Ошибка обработки сообщения: {e}")
            import traceback
            traceback.print_exc()
    
    async def listen(self):
        """Прослушивание сообщений"""
        try:
            if self.ws:
                print("👂 Начинаем прослушивание сообщений...")
                async for message in self.ws:
                    await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed as e:
            print(f"🔌 WebSocket соединение закрыто: {e}")
        except Exception as e:
            print(f"❌ Ошибка прослушивания: {e}")
            import traceback
            traceback.print_exc()
    
    async def disconnect(self):
        """Отключение от WebSocket"""
        if self.ws:
            await self.ws.close()
            print("🔌 Отключение от WebSocket")

async def monitor_futures_account():
    """Мониторинг фьючерсного аккаунта - показывает оригинальные JSON"""
    config = load_config()
    if not config:
        return
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return
    
    print("💰 МОНИТОРИНГ FUTURES АККАУНТА (JSON)")
    print("=" * 40)
    print("🔐 Требуется аутентификация для приватных данных")
    
    account_client = FuturesAccountChannel(config)
    
    try:
        if not await account_client.connect():
            return
        
        if not await account_client.authenticate():
            print("❌ Не удалось аутентифицироваться")
            return
        
        await asyncio.sleep(1)
        
        if not await account_client.subscribe_account():
            print("❌ Не удалось подписаться на аккаунт")
            return
        
        print("🔄 Мониторинг - показываем оригинальные JSON сообщения от биржи...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await account_client.listen()
        
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка мониторинга: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await account_client.disconnect()

async def equity_growth_tracker():
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
    
    print("📈 JSON ТРЕКЕР")
    print("=" * 40)
    
    duration = input("⏰ Время трекинга в секундах (по умолчанию 600): ").strip()
    try:
        duration = int(duration) if duration else 600
    except ValueError:
        duration = 600
    
    account_client = FuturesAccountChannel(config)
    
    try:
        if not await account_client.connect():
            return
        
        if not await account_client.authenticate():
            print("❌ Не удалось аутентифицироваться")
            return
        
        await account_client.subscribe_account()
        
        print(f"🔄 Показываем JSON сообщения в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(account_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\n⏰ Трекинг завершен")
        
    except KeyboardInterrupt:
        print("\n👋 Трекинг остановлен")
    finally:
        await account_client.disconnect()

async def main():
    """Основная функция"""
    print("💰 BITGET FUTURES ACCOUNT CHANNEL (JSON)")
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. 💰 Мониторинг аккаунта (JSON)")
    print("2. 📈 JSON трекер")
    
    try:
        choice = input("Ваш выбор (1-2): ").strip()
        
        if choice == "1":
            await monitor_futures_account()
        elif choice == "2":
            await equity_growth_tracker()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\n👋 Программа остановлена")

if __name__ == "__main__":
    asyncio.run(main())
