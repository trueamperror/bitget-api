#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures WebSocket - Account Channel (Private)

Канал для получения данных баланса фьючерсного аккаунта в реальном времени.
Требует аутентификации для получения приватных данных.

Документация: https://www.bitget.com/api-doc/contract/websocket/private/Account-Channel

Структура данных:
- marginCoin: валюта маржи (обычно USDT)
- locked: заблокированный баланс
- available: доступный баланс
- crossMargin: кросс-маржа
- isolatedMargin: изолированная маржа
- maxOpenPosAvailable: макс. доступно для открытия позиций
- equity: собственный капитал
- upl: нереализованная прибыль/убыток
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
        self.balance_history = []
        
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
        """Форматирование данных аккаунта"""
        if not data or 'data' not in data:
            return
        
        self.update_count += 1
        
        for account_update in data['data']:
            margin_coin = account_update.get('marginCoin', 'N/A')
            # Согласно документации Bitget, используются эти поля
            frozen = float(account_update.get('frozen', 0))  # заблокированные средства
            available = float(account_update.get('available', 0))  # доступные средства
            max_open_pos = float(account_update.get('maxOpenPosAvailable', 0))
            max_transfer_out = float(account_update.get('maxTransferOut', 0))
            equity = float(account_update.get('equity', 0))  # собственный капитал
            usdt_equity = float(account_update.get('usdtEquity', 0))  # капитал в USDT
            crossed_risk_rate = float(account_update.get('crossedRiskRate', 0))  # риск в кросс-режиме
            unrealized_pl = float(account_update.get('unrealizedPL', 0))  # нереализованная прибыль/убыток
            update_time = account_update.get('ts', 0)  # временная метка
            
            # Обновляем данные аккаунта
            self.account_data[margin_coin] = {
                'frozen': frozen,
                'available': available,
                'maxOpenPosAvailable': max_open_pos,
                'maxTransferOut': max_transfer_out,
                'equity': equity,
                'usdtEquity': usdt_equity,
                'crossedRiskRate': crossed_risk_rate,
                'unrealizedPL': unrealized_pl,
                'updateTime': update_time,
                'last_update': datetime.now()
            }
            
            # Сохраняем историю баланса
            self.balance_history.append({
                'equity': equity,
                'unrealizedPL': unrealized_pl,
                'available': available,
                'timestamp': datetime.now()
            })
            
            # Ограничиваем историю
            if len(self.balance_history) > 100:
                self.balance_history = self.balance_history[-50:]
            
            # Форматирование времени
            if update_time:
                dt = datetime.fromtimestamp(int(update_time) / 1000)
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Общий баланс
            total_balance = available + frozen
            
            print(f"\\n💰 [{time_str}] FUTURES АККАУНТ #{self.update_count}")
            print(f"🪙 Валюта: {margin_coin}")
            print(f"💵 Собственный капитал: ${equity:,.2f}")
            print(f"💰 Доступно: ${available:,.2f}")
            print(f"🔒 Заблокировано: ${frozen:,.2f}")
            print(f"📊 Общий баланс: ${total_balance:,.2f}")
            
            # PnL информация
            upl_emoji = "🟢" if unrealized_pl >= 0 else "🔴"
            print(f"{upl_emoji} Нереализованный PnL: ${unrealized_pl:+,.2f}")
            
            # Дополнительная информация
            if max_open_pos > 0:
                print(f"🎯 Доступно для позиций: ${max_open_pos:,.2f}")
                pos_percentage = (max_open_pos / equity) * 100 if equity > 0 else 0
                print(f"� % от капитала: {pos_percentage:.2f}%")
            
            if max_transfer_out > 0:
                print(f"� Макс. вывод: ${max_transfer_out:,.2f}")
            
            if crossed_risk_rate > 0:
                print(f"⚠️ Риск кросс-маржи: {crossed_risk_rate:.4f}")
            
            if usdt_equity != equity:
                print(f"� Капитал в USDT: ${usdt_equity:,.2f}")
            
            # Показываем расширенную статистику каждые 10 обновлений
            if self.update_count % 10 == 0:
                self.show_account_analytics()
            
            print("─" * 50)
    
    def show_account_analytics(self):
        """Показать аналитику аккаунта"""
        if len(self.balance_history) < 5:
            return
        
        print(f"\\n📈 АНАЛИТИКА АККАУНТА (обновлено: {datetime.now().strftime('%H:%M:%S')})")
        print("=" * 60)
        
        # Статистика по последним 10 записям
        recent_history = self.balance_history[-10:]
        
        equity_values = [entry['equity'] for entry in recent_history]
        upl_values = [entry['unrealizedPL'] for entry in recent_history]
        
        if len(equity_values) > 1:
            equity_change = equity_values[-1] - equity_values[0]
            equity_change_percent = (equity_change / equity_values[0]) * 100 if equity_values[0] > 0 else 0
            
            avg_equity = sum(equity_values) / len(equity_values)
            max_equity = max(equity_values)
            min_equity = min(equity_values)
            
            print(f"💰 Динамика капитала (последние {len(equity_values)} обновлений):")
            print(f"   Изменение: ${equity_change:+,.2f} ({equity_change_percent:+.2f}%)")
            print(f"   Средний: ${avg_equity:,.2f}")
            print(f"   Максимум: ${max_equity:,.2f}")
            print(f"   Минимум: ${min_equity:,.2f}")
        
        # Анализ PnL
        if upl_values:
            current_upl = upl_values[-1]
            max_upl = max(upl_values)
            min_upl = min(upl_values)
            
            print(f"\\n📊 Анализ PnL:")
            print(f"   Текущий: ${current_upl:+,.2f}")
            print(f"   Лучший: ${max_upl:+,.2f}")
            print(f"   Худший: ${min_upl:+,.2f}")
            print(f"   Размах: ${max_upl - min_upl:,.2f}")
        
        # Определение тренда
        if len(equity_values) >= 3:
            recent_trend = equity_values[-3:]
            if all(recent_trend[i] <= recent_trend[i+1] for i in range(len(recent_trend)-1)):
                trend = "📈 ВОСХОДЯЩИЙ"
            elif all(recent_trend[i] >= recent_trend[i+1] for i in range(len(recent_trend)-1)):
                trend = "📉 НИСХОДЯЩИЙ"
            else:
                trend = "📊 БОКОВОЙ"
            
            print(f"\\n📈 Тренд капитала: {trend}")
        
        # Риск-метрики
        current_account = list(self.account_data.values())[0] if self.account_data else None
        if current_account:
            equity = current_account['equity']
            crossed_risk_rate = current_account['crossedRiskRate']
            
            if equity > 0 and crossed_risk_rate > 0:
                risk_level = ""
                
                if crossed_risk_rate < 0.1:
                    risk_level = "🟢 НИЗКИЙ"
                elif crossed_risk_rate < 0.3:
                    risk_level = "🟡 УМЕРЕННЫЙ"
                elif crossed_risk_rate < 0.5:
                    risk_level = "🟠 ПОВЫШЕННЫЙ"
                else:
                    risk_level = "🔴 ВЫСОКИЙ"
                
                print(f"\\n⚠️ Риск-анализ:")
                print(f"   Коэффициент риска: {crossed_risk_rate:.4f}")
                print(f"   Уровень риска: {risk_level}")
    
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
            
            # Обработка ошибок
            elif data.get('event') == 'error':
                print(f"❌ Ошибка сервера: {data.get('msg', 'Unknown error')}")
            
            # Обработка данных аккаунта
            elif data.get('action') in ['snapshot', 'update']:
                channel = data.get('arg', {}).get('channel', '')
                if channel == 'account':
                    self.format_account_data(data)
                else:
                    print(f"🤔 Неожиданный канал: {channel}")
            
            # Пинг-понг
            elif 'ping' in data:
                pong_message = {'pong': data['ping']}
                if self.ws:
                    await self.ws.send(json.dumps(pong_message))
            
            # Любые другие сообщения
            else:
                print(f"ℹ️ Неизвестное сообщение: {data}")
        
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
            print(f"🔌 Отключение от WebSocket. Обновлений: {self.update_count}")
            
            # Финальная аналитика
            self.show_account_analytics()


async def monitor_futures_account():
    """Мониторинг фьючерсного аккаунта"""
    config = load_config()
    if not config:
        return
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return
    
    print("💰 МОНИТОРИНГ FUTURES АККАУНТА")
    print("=" * 40)
    print("🔐 Требуется аутентификация для приватных данных")
    
    account_client = FuturesAccountChannel(config)
    
    try:
        if not await account_client.connect():
            return
        
        # Ждем успешной аутентификации
        if not await account_client.authenticate():
            print("❌ Не удалось аутентифицироваться")
            return
        
        # Небольшая пауза после аутентификации
        await asyncio.sleep(1)
        
        # Подписываемся на аккаунт
        if not await account_client.subscribe_account():
            print("❌ Не удалось подписаться на аккаунт")
            return
        
        print("🔄 Мониторинг баланса фьючерсного аккаунта...")
        print("💡 Нажмите Ctrl+C для остановки")
        print("📊 Откройте/закройте позицию для получения обновлений...")
        
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
    """Трекер роста капитала"""
    config = load_config()
    if not config:
        return
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return
    
    print("📈 ТРЕКЕР РОСТА КАПИТАЛА")
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
        
        # Ждем успешной аутентификации
        if not await account_client.authenticate():
            print("❌ Не удалось аутентифицироваться")
            return
        
        # Подписываемся на аккаунт
        await account_client.subscribe_account()
        
        print(f"🔄 Трекинг роста капитала в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        start_time = time.time()
        initial_equity = None
        
        try:
            await asyncio.wait_for(account_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            end_time = time.time()
            session_duration = end_time - start_time
            
            print(f"\\n⏰ Трекинг завершен ({session_duration:.0f} сек)")
            
            # Анализ роста
            if account_client.balance_history:
                initial_equity = account_client.balance_history[0]['equity']
                final_equity = account_client.balance_history[-1]['equity']
                
                growth = final_equity - initial_equity
                growth_percent = (growth / initial_equity) * 100 if initial_equity > 0 else 0
                
                print(f"\\n📊 РЕЗУЛЬТАТЫ ТРЕКИНГА:")
                print(f"💰 Начальный капитал: ${initial_equity:,.2f}")
                print(f"💰 Финальный капитал: ${final_equity:,.2f}")
                print(f"📈 Изменение: ${growth:+,.2f} ({growth_percent:+.2f}%)")
                
                # Оценка производительности
                if growth_percent > 5:
                    performance = "🚀 ОТЛИЧНЫЙ РОСТ"
                elif growth_percent > 1:
                    performance = "🟢 ПОЛОЖИТЕЛЬНЫЙ РОСТ"
                elif growth_percent > -1:
                    performance = "⚪ СТАБИЛЬНОСТЬ"
                elif growth_percent > -5:
                    performance = "🟠 НЕБОЛЬШОЙ УБЫТОК"
                else:
                    performance = "🔴 ЗНАЧИТЕЛЬНЫЙ УБЫТОК"
                
                print(f"📊 Оценка: {performance}")
                
                # Среднечасовая доходность
                hours = session_duration / 3600
                if hours > 0:
                    hourly_return = growth_percent / hours
                    print(f"⏰ Среднечасовая доходность: {hourly_return:+.2f}%")
            else:
                print("📭 Недостаточно данных для анализа")
        
    except KeyboardInterrupt:
        print("\\n👋 Трекинг остановлен")
    finally:
        await account_client.disconnect()


async def main():
    """Основная функция"""
    print("💰 BITGET FUTURES ACCOUNT CHANNEL")
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. 💰 Мониторинг аккаунта")
    print("2. 📈 Трекер роста капитала")
    
    try:
        choice = input("Ваш выбор (1-2): ").strip()
        
        if choice == "1":
            await monitor_futures_account()
        elif choice == "2":
            await equity_growth_tracker()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")


if __name__ == "__main__":
    asyncio.run(main())
