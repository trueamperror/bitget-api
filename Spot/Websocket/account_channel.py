#!/usr/bin/env python3
"""
Bitget Spot WebSocket - Account Channel (Private)

Канал для получения данных баланса аккаунта в реальном времени.
Требует аутентификации для получения приватных данных.

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
        self.balance_data = {}
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
        """Форматирование данных баланса"""
        if not data or 'data' not in data:
            return
        
        self.update_count += 1
        
        for balance_update in data['data']:
            coin = balance_update.get('coin', 'N/A')
            available = float(balance_update.get('available', 0))
            frozen = float(balance_update.get('frozen', 0))
            locked = float(balance_update.get('locked', 0))
            
            total = available + frozen + locked
            
            # Обновляем данные баланса
            self.balance_data[coin] = {
                'available': available,
                'frozen': frozen,
                'locked': locked,
                'total': total,
                'last_update': datetime.now()
            }
            
            # Показываем только значимые балансы (больше 0.001)
            if total > 0.001:
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                print(f"\\n💰 [{time_str}] БАЛАНС #{self.update_count}")
                print(f"🪙 Валюта: {coin}")
                print(f"✅ Доступно: {available:,.6f}")
                if frozen > 0:
                    print(f"❄️ Заморожено: {frozen:,.6f}")
                if locked > 0:
                    print(f"🔒 Заблокировано: {locked:,.6f}")
                print(f"📊 Всего: {total:,.6f}")
                print("─" * 40)
                
                # Показываем сводку каждые 10 обновлений
                if self.update_count % 10 == 0:
                    self.show_portfolio_summary()
    
    def show_portfolio_summary(self):
        """Показать сводку портфеля"""
        if not self.balance_data:
            return
        
        print(f"\\n📊 СВОДКА ПОРТФЕЛЯ (обновлено: {datetime.now().strftime('%H:%M:%S')})")
        print("=" * 60)
        
        # Фильтруем значимые балансы
        significant_balances = {
            coin: data for coin, data in self.balance_data.items() 
            if data['total'] > 0.001
        }
        
        if not significant_balances:
            print("📭 Нет значимых балансов")
            return
        
        print(f"💼 Валют в портфеле: {len(significant_balances)}")
        print(f"🔄 Всего обновлений: {self.update_count}")
        
        print(f"\\n{'Валюта':^10} {'Доступно':>15} {'Заморожено':>15} {'Всего':>15}")
        print("─" * 65)
        
        # Сортируем по общему балансу
        sorted_balances = sorted(
            significant_balances.items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )
        
        for coin, data in sorted_balances:
            available = data['available']
            frozen = data['frozen']
            total = data['total']
            
            print(f"{coin:^10} {available:>15.6f} {frozen:>15.6f} {total:>15.6f}")
        
        # Статистика валют
        usdt_balance = significant_balances.get('USDT', {}).get('total', 0)
        btc_balance = significant_balances.get('BTC', {}).get('total', 0)
        eth_balance = significant_balances.get('ETH', {}).get('total', 0)
        
        print(f"\\n💵 Основные балансы:")
        if usdt_balance > 0:
            print(f"💲 USDT: {usdt_balance:,.2f}")
        if btc_balance > 0:
            print(f"₿ BTC: {btc_balance:.6f}")
        if eth_balance > 0:
            print(f"Ξ ETH: {eth_balance:.6f}")
    
    async def handle_message(self, message):
        """Обработка входящих сообщений"""
        try:
            data = json.loads(message)
            
            # Обработка ответа аутентификации
            if data.get('event') == 'login':
                if data.get('code') == '0':
                    print("✅ Аутентификация успешна!")
                    await self.subscribe_account()
                else:
                    print(f"❌ Ошибка аутентификации: {data.get('msg', 'Unknown error')}")
                    return False
            
            # Обработка ответа на подписку
            elif data.get('event') == 'subscribe':
                if data.get('code') == '0':
                    channel = data.get('arg', {}).get('channel', 'unknown')
                    print(f"✅ Подписка успешна: {channel}")
                else:
                    print(f"❌ Ошибка подписки: {data.get('msg', 'Unknown error')}")
            
            # Обработка данных баланса
            elif data.get('action') in ['snapshot', 'update']:
                channel = data.get('arg', {}).get('channel', '')
                if channel == 'account':
                    self.format_balance_data(data)
            
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
            self.show_portfolio_summary()


async def monitor_account_balance():
    """Мониторинг изменений баланса аккаунта"""
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
    """Трекер баланса с таймером"""
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
    print("💰 BITGET SPOT ACCOUNT CHANNEL")
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
