#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures WebSocket - Plan Orders Channel (Private)

Канал для получения обновлений по плановым ордерам (стоп-лосс, тейк-профит) фьючерсов.
Требует аутентификации для получения приватных данных.

Документация: https://www.bitget.com/api-doc/contract/websocket/private/Plan-Orders-Channel

Структура данных:
- orderId: ID планового ордера
- planOrderId: ID планового ордера
- symbol: торговая пара
- marginMode: режим маржи
- marginCoin: валюта маржи
- size: размер ордера
- price: цена ордера
- triggerPrice: цена срабатывания
- triggerType: тип триггера
- side: сторона (buy/sell)
- orderType: тип ордера
- timeInForce: время действия
- planType: тип планового ордера
- state: состояние ордера
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


class FuturesPlanOrdersChannel:
    def __init__(self, config):
        self.config = config
        self.ws = None
        self.plan_orders_data = {}
        self.update_count = 0
        self.orders_stats = {
            'total_orders': 0,
            'stop_loss_orders': 0,
            'take_profit_orders': 0,
            'profit_stop_orders': 0,
            'conditional_orders': 0,
            'active_orders': 0,
            'triggered_orders': 0,
            'cancelled_orders': 0,
            'pairs_monitored': set(),
            'avg_trigger_distance': 0
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
    
    async def subscribe_plan_orders(self, symbol=None):
        """Подписка на плановые ордера фьючерсов"""
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "instType": "USDT-FUTURES",
                    "channel": "orders-algo",
                    "instId": symbol if symbol else "default"
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
            if symbol:
                print(f"📡 Подписка на плановые ордера фьючерса {symbol}")
            else:
                print("📡 Подписка на все плановые ордера фьючерсов")
    
    def format_plan_order_data(self, data):
        """Форматирование данных плановых ордеров"""
        if not data or 'data' not in data:
            return
        
        for order in data['data']:
            self.update_count += 1
            
            order_id = order.get('orderId', 'N/A')
            plan_order_id = order.get('planOrderId', 'N/A')
            symbol = order.get('symbol', 'N/A')
            margin_mode = order.get('marginMode', 'N/A')
            margin_coin = order.get('marginCoin', 'N/A')
            size = float(order.get('size', 0))
            price = float(order.get('price', 0))
            trigger_price = float(order.get('triggerPrice', 0))
            trigger_type = order.get('triggerType', 'N/A')
            side = order.get('side', 'N/A')
            order_type = order.get('orderType', 'N/A')
            time_in_force = order.get('timeInForce', 'N/A')
            plan_type = order.get('planType', 'N/A')
            state = order.get('state', 'N/A')
            reduce_only = order.get('reduceOnly', False)
            
            # Обновляем статистику
            self.update_order_stats(plan_type, state, symbol, trigger_price, price)
            
            # Сохраняем данные ордера
            order_key = plan_order_id if plan_order_id != 'N/A' else order_id
            self.plan_orders_data[order_key] = {
                'orderId': order_id,
                'planOrderId': plan_order_id,
                'symbol': symbol,
                'marginMode': margin_mode,
                'marginCoin': margin_coin,
                'size': size,
                'price': price,
                'triggerPrice': trigger_price,
                'triggerType': trigger_type,
                'side': side,
                'orderType': order_type,
                'timeInForce': time_in_force,
                'planType': plan_type,
                'state': state,
                'reduceOnly': reduce_only,
                'timestamp': datetime.now()
            }
            
            # Эмодзи для типа ордера
            type_emoji = self.get_order_type_emoji(plan_type, side)
            
            # Эмодзи для состояния
            state_emoji = self.get_state_emoji(state)
            
            # Расчет дистанции до триггера (в процентах)
            trigger_distance = ""
            if trigger_price > 0 and price > 0:
                distance_percent = abs((trigger_price - price) / price) * 100
                trigger_distance = f"📏 Дистанция: {distance_percent:.2f}%"
            
            time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            print(f"\\n{type_emoji} [{time_str}] ПЛАНОВЫЙ ОРДЕР #{self.update_count}")
            print(f"💱 {symbol}")
            print(f"🆔 Order ID: {order_id[-12:] if len(order_id) > 12 else order_id}")
            print(f"🎯 Plan ID: {plan_order_id[-12:] if len(plan_order_id) > 12 else plan_order_id}")
            print(f"{state_emoji} Состояние: {state.upper()}")
            print(f"📋 Тип: {plan_type.upper()} │ Сторона: {side.upper()}")
            print(f"💰 Цена ордера: ${price:,.4f}")
            print(f"🎯 Триггер: ${trigger_price:,.4f} ({trigger_type})")
            print(f"📊 Размер: {size:,.0f} контрактов")
            print(f"⚖️ Маржа: {margin_mode} ({margin_coin})")
            
            if trigger_distance:
                print(trigger_distance)
            
            # Специальные флаги
            flags = []
            if reduce_only:
                flags.append("🔒 ЗАКРЫТИЕ")
            if time_in_force != 'GTC':
                flags.append(f"⏰ {time_in_force}")
            
            if flags:
                print(f"🏷️ Флаги: {' │ '.join(flags)}")
            
            # Показываем статистику каждые 5 обновлений
            if self.update_count % 5 == 0:
                self.show_orders_summary()
            
            print("─" * 60)
    
    def get_order_type_emoji(self, plan_type, side):
        """Получить эмодзи для типа ордера"""
        if 'stop' in plan_type.lower():
            return "🛑"  # Стоп-ордер
        elif 'profit' in plan_type.lower():
            return "💎"  # Тейк-профит
        elif 'conditional' in plan_type.lower():
            return "🎯"  # Условный ордер
        elif side.lower() == 'buy':
            return "📈"  # Покупка
        else:
            return "📉"  # Продажа
    
    def get_state_emoji(self, state):
        """Получить эмодзи для состояния ордера"""
        state_lower = state.lower()
        if state_lower in ['live', 'new', 'active']:
            return "🟢"  # Активный
        elif state_lower in ['triggered', 'filled']:
            return "✅"  # Исполнен
        elif state_lower in ['cancelled', 'canceled']:
            return "❌"  # Отменен
        elif state_lower in ['expired']:
            return "⏰"  # Истек
        elif state_lower in ['pending']:
            return "🟡"  # Ожидание
        else:
            return "⚪"  # Неизвестно
    
    def update_order_stats(self, plan_type, state, symbol, trigger_price, price):
        """Обновить статистику ордеров"""
        self.orders_stats['total_orders'] += 1
        self.orders_stats['pairs_monitored'].add(symbol)
        
        # Классификация по типу
        plan_type_lower = plan_type.lower()
        if 'stop' in plan_type_lower and 'loss' in plan_type_lower:
            self.orders_stats['stop_loss_orders'] += 1
        elif 'profit' in plan_type_lower:
            self.orders_stats['take_profit_orders'] += 1
        elif 'stop' in plan_type_lower:
            self.orders_stats['profit_stop_orders'] += 1
        else:
            self.orders_stats['conditional_orders'] += 1
        
        # Состояния
        state_lower = state.lower()
        if state_lower in ['live', 'new', 'active']:
            self.orders_stats['active_orders'] += 1
        elif state_lower in ['triggered', 'filled']:
            self.orders_stats['triggered_orders'] += 1
        elif state_lower in ['cancelled', 'canceled']:
            self.orders_stats['cancelled_orders'] += 1
        
        # Средняя дистанция до триггера
        if trigger_price > 0 and price > 0:
            distance_percent = abs((trigger_price - price) / price) * 100
            current_avg = self.orders_stats['avg_trigger_distance']
            count = self.orders_stats['total_orders']
            self.orders_stats['avg_trigger_distance'] = ((current_avg * (count - 1)) + distance_percent) / count
    
    def show_orders_summary(self):
        """Показать сводку по ордерам"""
        stats = self.orders_stats
        
        print(f"\\n📊 СВОДКА ПЛАНОВЫХ ОРДЕРОВ (обновлено: {datetime.now().strftime('%H:%M:%S')})")
        print("=" * 70)
        
        print(f"🎯 Всего ордеров: {stats['total_orders']}")
        print(f"🔄 Всего обновлений: {self.update_count}")
        print(f"💱 Торговых пар: {len(stats['pairs_monitored'])}")
        
        # Распределение по типам
        if stats['total_orders'] > 0:
            print(f"\\n📋 Типы ордеров:")
            print(f"🛑 Стоп-лосс: {stats['stop_loss_orders']}")
            print(f"💎 Тейк-профит: {stats['take_profit_orders']}")
            print(f"🔄 Профит-стоп: {stats['profit_stop_orders']}")
            print(f"🎯 Условные: {stats['conditional_orders']}")
            
            # Состояния ордеров
            print(f"\\n🔍 Состояния ордеров:")
            print(f"🟢 Активных: {stats['active_orders']}")
            print(f"✅ Исполнено: {stats['triggered_orders']}")
            print(f"❌ Отменено: {stats['cancelled_orders']}")
            
            # Эффективность
            if stats['triggered_orders'] + stats['cancelled_orders'] > 0:
                success_rate = (stats['triggered_orders'] / (stats['triggered_orders'] + stats['cancelled_orders'])) * 100
                print(f"\\n📈 Эффективность исполнения: {success_rate:.1f}%")
            
            # Средняя дистанция
            if stats['avg_trigger_distance'] > 0:
                print(f"📏 Средняя дистанция до триггера: {stats['avg_trigger_distance']:.2f}%")
                
                # Анализ дистанции
                if stats['avg_trigger_distance'] < 1:
                    distance_analysis = "🔥 ОЧЕНЬ БЛИЗКО"
                elif stats['avg_trigger_distance'] < 3:
                    distance_analysis = "⚡ БЛИЗКО"
                elif stats['avg_trigger_distance'] < 10:
                    distance_analysis = "📊 УМЕРЕННО"
                else:
                    distance_analysis = "📏 ДАЛЕКО"
                
                print(f"🎯 Анализ дистанции: {distance_analysis}")
        
        # Активные пары
        if stats['pairs_monitored']:
            pairs_list = ', '.join(list(stats['pairs_monitored'])[:5])
            if len(stats['pairs_monitored']) > 5:
                pairs_list += f" и еще {len(stats['pairs_monitored']) - 5}"
            print(f"\\n💱 Активные пары: {pairs_list}")
        
        # Стратегический анализ
        if stats['total_orders'] > 0:
            sl_ratio = stats['stop_loss_orders'] / stats['total_orders']
            tp_ratio = stats['take_profit_orders'] / stats['total_orders']
            
            if sl_ratio > 0.6:
                strategy_type = "🛡️ ЗАЩИТНАЯ СТРАТЕГИЯ"
            elif tp_ratio > 0.6:
                strategy_type = "💎 ПРИБЫЛЬНАЯ СТРАТЕГИЯ"
            elif abs(sl_ratio - tp_ratio) < 0.2:
                strategy_type = "⚖️ СБАЛАНСИРОВАННАЯ СТРАТЕГИЯ"
            else:
                strategy_type = "🎯 СМЕШАННАЯ СТРАТЕГИЯ"
            
            print(f"\\n📊 Тип стратегии: {strategy_type}")
    
    def show_active_orders(self, count=10):
        """Показать активные ордера"""
        active_orders = {
            k: v for k, v in self.plan_orders_data.items()
            if v['state'].lower() in ['live', 'new', 'active']
        }
        
        if not active_orders:
            print("\\n📭 Активных ордеров не найдено")
            return
        
        recent_orders = sorted(
            active_orders.items(),
            key=lambda x: x[1]['timestamp'],
            reverse=True
        )[:count]
        
        print(f"\\n🟢 АКТИВНЫЕ ОРДЕРА ({len(active_orders)} всего):")
        print(f"{'Plan ID':^15} {'Пара':^12} {'Тип':^12} {'Триггер':>12} {'Дист %':>8}")
        print("─" * 75)
        
        for plan_id, data in recent_orders:
            short_id = plan_id[-8:] if len(plan_id) > 8 else plan_id
            
            # Расчет дистанции
            if data['triggerPrice'] > 0 and data['price'] > 0:
                distance = abs((data['triggerPrice'] - data['price']) / data['price']) * 100
                distance_str = f"{distance:.1f}%"
            else:
                distance_str = "N/A"
            
            print(f"{short_id:^15} {data['symbol']:^12} {data['planType'][:10]:^12} {data['triggerPrice']:>12.4f} {distance_str:>8}")
    
    async def handle_message(self, message):
        """Обработка входящих сообщений"""
        try:
            data = json.loads(message)
            
            # Обработка ответа аутентификации
            if data.get('event') == 'login':
                if data.get('code') == '0':
                    print("✅ Аутентификация успешна!")
                    await self.subscribe_plan_orders()
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
            
            # Обработка данных плановых ордеров
            elif data.get('action') in ['snapshot', 'update']:
                channel = data.get('arg', {}).get('channel', '')
                if channel == 'orders-algo':
                    self.format_plan_order_data(data)
            
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
            self.show_active_orders()


async def monitor_all_plan_orders():
    """Мониторинг всех плановых ордеров"""
    config = load_config()
    if not config:
        return
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return
    
    print("🎯 МОНИТОРИНГ ПЛАНОВЫХ ОРДЕРОВ FUTURES")
    print("=" * 40)
    print("🔐 Требуется аутентификация для приватных данных")
    
    plan_orders_client = FuturesPlanOrdersChannel(config)
    
    try:
        if not await plan_orders_client.connect():
            return
        
        await plan_orders_client.authenticate()
        
        print("🔄 Мониторинг плановых ордеров...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await plan_orders_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await plan_orders_client.disconnect()


async def risk_management_analysis():
    """Анализ риск-менеджмента через плановые ордера"""
    config = load_config()
    if not config:
        return
    
    # Проверяем наличие необходимых ключей
    required_keys = ['apiKey', 'secretKey', 'passphrase']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ Отсутствует {key} в конфигурации")
            return
    
    print("🛡️ АНАЛИЗ РИСК-МЕНЕДЖМЕНТА")
    print("=" * 40)
    
    duration = input("⏰ Время анализа в секундах (по умолчанию 300): ").strip()
    try:
        duration = int(duration) if duration else 300
    except ValueError:
        duration = 300
    
    plan_orders_client = FuturesPlanOrdersChannel(config)
    
    try:
        if not await plan_orders_client.connect():
            return
        
        await plan_orders_client.authenticate()
        await asyncio.sleep(1)
        await plan_orders_client.subscribe_plan_orders()
        
        print(f"🔄 Анализ риск-менеджмента в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(plan_orders_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\\n⏰ Анализ завершен ({duration} сек)")
            
            # Детальный анализ риск-менеджмента
            stats = plan_orders_client.orders_stats
            
            if stats['total_orders'] > 0:
                print(f"\\n🛡️ РЕЗУЛЬТАТЫ АНАЛИЗА РИСК-МЕНЕДЖМЕНТА:")
                
                # Соотношение защитных и доходных ордеров
                protective_orders = stats['stop_loss_orders'] + stats['profit_stop_orders']
                profit_orders = stats['take_profit_orders']
                
                if stats['total_orders'] > 0:
                    protective_ratio = protective_orders / stats['total_orders']
                    profit_ratio = profit_orders / stats['total_orders']
                    
                    print(f"🛑 Защитные ордера: {protective_orders} ({protective_ratio:.1%})")
                    print(f"💎 Доходные ордера: {profit_orders} ({profit_ratio:.1%})")
                    
                    # Оценка качества риск-менеджмента
                    if protective_ratio > 0.7:
                        risk_quality = "🟢 ОТЛИЧНЫЙ - Высокий уровень защиты"
                    elif protective_ratio > 0.5:
                        risk_quality = "🟡 ХОРОШИЙ - Адекватная защита"
                    elif protective_ratio > 0.3:
                        risk_quality = "🟠 СРЕДНИЙ - Недостаточная защита"
                    else:
                        risk_quality = "🔴 ПЛОХОЙ - Критически низкая защита"
                    
                    print(f"\\n🎯 Качество риск-менеджмента: {risk_quality}")
                    
                    # Анализ дистанции триггеров
                    if stats['avg_trigger_distance'] > 0:
                        print(f"📏 Средняя дистанция триггеров: {stats['avg_trigger_distance']:.2f}%")
                        
                        if stats['avg_trigger_distance'] < 2:
                            distance_risk = "🔴 ВЫСОКИЙ РИСК - Слишком близкие триггеры"
                        elif stats['avg_trigger_distance'] < 5:
                            distance_risk = "🟡 УМЕРЕННЫЙ РИСК - Близкие триггеры"
                        elif stats['avg_trigger_distance'] < 15:
                            distance_risk = "🟢 НИЗКИЙ РИСК - Адекватные триггеры"
                        else:
                            distance_risk = "🟠 СРЕДНИЙ РИСК - Далекие триггеры"
                        
                        print(f"⚠️ Риск триггеров: {distance_risk}")
                    
                    # Эффективность исполнения
                    executed_cancelled = stats['triggered_orders'] + stats['cancelled_orders']
                    if executed_cancelled > 0:
                        execution_rate = stats['triggered_orders'] / executed_cancelled
                        
                        if execution_rate > 0.8:
                            execution_quality = "🟢 ОТЛИЧНАЯ - Высокая точность"
                        elif execution_rate > 0.6:
                            execution_quality = "🟡 ХОРОШАЯ - Приемлемая точность"
                        elif execution_rate > 0.4:
                            execution_quality = "🟠 СРЕДНЯЯ - Низкая точность"
                        else:
                            execution_quality = "🔴 ПЛОХАЯ - Очень низкая точность"
                        
                        print(f"🎯 Эффективность исполнения: {execution_rate:.1%} - {execution_quality}")
                
                # Рекомендации
                print(f"\\n💡 РЕКОМЕНДАЦИИ:")
                
                if protective_ratio < 0.5:
                    print("• Увеличьте количество защитных ордеров")
                
                if stats['avg_trigger_distance'] < 3:
                    print("• Рассмотрите увеличение дистанции триггеров")
                elif stats['avg_trigger_distance'] > 20:
                    print("• Рассмотрите уменьшение дистанции триггеров")
                
                if stats['cancelled_orders'] > stats['triggered_orders']:
                    print("• Пересмотрите стратегию размещения ордеров")
                
                if len(stats['pairs_monitored']) > 10:
                    print("• Рассмотрите сокращение количества отслеживаемых пар")
            else:
                print("📭 Данных о плановых ордерах не найдено")
        
    except KeyboardInterrupt:
        print("\\n👋 Анализ остановлен")
    finally:
        await plan_orders_client.disconnect()


async def main():
    """Основная функция"""
    print("🎯 BITGET FUTURES PLAN ORDERS CHANNEL")
    print("=" * 40)
    
    print("🔌 Выберите режим мониторинга:")
    print("1. 🎯 Все плановые ордера")
    print("2. 🛡️ Анализ риск-менеджмента")
    
    try:
        choice = input("Ваш выбор (1-2): ").strip()
        
        if choice == "1":
            await monitor_all_plan_orders()
        elif choice == "2":
            await risk_management_analysis()
        else:
            print("❌ Неверный выбор")
    
    except KeyboardInterrupt:
        print("\\n👋 Программа остановлена")


if __name__ == "__main__":
    asyncio.run(main())
