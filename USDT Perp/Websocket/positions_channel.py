#!/usr/bin/env python3
"""
Bitget USDT Perpetual Futures WebSocket - Positions Channel (Private)

Канал для получения данных позиций в реальном времени.
Требует аутентификации для получения приватных данных.

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
        self.positions_data = {}
        self.update_count = 0
        self.pnl_history = {}
        
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
                    "instId": symbol if symbol else "default"
                }
            ]
        }
        
        if self.ws:
            await self.ws.send(json.dumps(subscribe_message))
            if symbol:
                print(f"📡 Подписка на позиции для {symbol}")
            else:
                print("📡 Подписка на все позиции")
    
    def get_position_emoji(self, side, unrealized_pl):
        """Получить эмодзи для позиции"""
        if side.lower() == 'long':
            return "🟢" if unrealized_pl >= 0 else "🔴"
        else:
            return "🔴" if unrealized_pl >= 0 else "🟢"
    
    def format_position_data(self, data):
        """Форматирование данных позиций"""
        if not data or 'data' not in data:
            return
        
        for position in data['data']:
            self.update_count += 1
            
            symbol = position.get('symbol', 'N/A')
            size = float(position.get('size', 0))
            side = position.get('side', 'N/A')
            mark_price = float(position.get('markPrice', 0))
            avg_price = float(position.get('avgPrice', 0))
            leverage = float(position.get('leverage', 0))
            margin_mode = position.get('marginMode', 'N/A')
            unrealized_pl = float(position.get('unrealizedPL', 0))
            percentage = float(position.get('percentage', 0))
            margin = float(position.get('margin', 0))
            available = float(position.get('available', 0))
            locked = float(position.get('locked', 0))
            update_time = position.get('uTime', 0)
            
            # Пропускаем пустые позиции
            if size == 0:
                continue
            
            # Обновляем данные позиции
            self.positions_data[symbol] = {
                'size': size,
                'side': side,
                'markPrice': mark_price,
                'avgPrice': avg_price,
                'leverage': leverage,
                'marginMode': margin_mode,
                'unrealizedPL': unrealized_pl,
                'percentage': percentage,
                'margin': margin,
                'available': available,
                'locked': locked,
                'updateTime': update_time,
                'last_update': datetime.now()
            }
            
            # Сохраняем историю PnL
            if symbol not in self.pnl_history:
                self.pnl_history[symbol] = []
            self.pnl_history[symbol].append({
                'pnl': unrealized_pl,
                'percentage': percentage,
                'price': mark_price,
                'timestamp': datetime.now()
            })
            
            # Ограничиваем историю
            if len(self.pnl_history[symbol]) > 100:
                self.pnl_history[symbol] = self.pnl_history[symbol][-50:]
            
            # Форматирование времени
            if update_time:
                dt = datetime.fromtimestamp(int(update_time) / 1000)
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Получаем эмодзи для позиции
            position_emoji = self.get_position_emoji(side, unrealized_pl)
            side_arrow = "📈" if side.lower() == 'long' else "📉"
            
            # Расчет стоимости позиции
            position_value = mark_price * size
            
            print(f"\\n🎯 [{time_str}] ПОЗИЦИЯ #{self.update_count}")
            print(f"💱 {symbol}")
            print(f"{side_arrow} Сторона: {position_emoji} {side.upper()} │ Плечо: {leverage:.0f}x")
            print(f"📊 Размер: {size:,.4f} │ Стоимость: ${position_value:,.2f}")
            print(f"💰 Вход: ${avg_price:,.4f} │ Текущая: ${mark_price:,.4f}")
            print(f"💵 Маржа: ${margin:,.2f} ({margin_mode})")
            print(f"📈 PnL: ${unrealized_pl:+,.2f} ({percentage:+.2f}%)")
            
            # Доступность для закрытия
            if available > 0:
                print(f"✅ Доступно: {available:,.4f}")
            if locked > 0:
                print(f"🔒 Заблокировано: {locked:,.4f}")
            
            # Индикатор производительности
            if percentage > 10:
                performance = "🚀 ОТЛИЧНАЯ ПРИБЫЛЬ"
            elif percentage > 2:
                performance = "🟢 ПРИБЫЛЬ"
            elif percentage > -2:
                performance = "⚪ ОКОЛО НУЛЯ"
            elif percentage > -10:
                performance = "🟠 УБЫТОК"
            else:
                performance = "🔴 КРУПНЫЙ УБЫТОК"
            
            print(f"📊 Статус: {performance}")
            
            # Показываем сводку каждые 5 обновлений
            if self.update_count % 5 == 0:
                self.show_portfolio_summary()
            
            print("─" * 60)
    
    def show_portfolio_summary(self):
        """Показать сводку портфеля позиций"""
        if not self.positions_data:
            print("\\n📭 Нет открытых позиций")
            return
        
        print(f"\\n📊 СВОДКА ПОРТФЕЛЯ (обновлено: {datetime.now().strftime('%H:%M:%S')})")
        print("=" * 70)
        
        total_positions = len(self.positions_data)
        total_pnl = sum(pos['unrealizedPL'] for pos in self.positions_data.values())
        total_margin = sum(pos['margin'] for pos in self.positions_data.values())
        long_positions = sum(1 for pos in self.positions_data.values() if pos['side'].lower() == 'long')
        short_positions = total_positions - long_positions
        
        print(f"🎯 Всего позиций: {total_positions}")
        print(f"📈 Длинные позиции: {long_positions}")
        print(f"📉 Короткие позиции: {short_positions}")
        print(f"💰 Общая маржа: ${total_margin:,.2f}")
        print(f"💵 Общий PnL: ${total_pnl:+,.2f}")
        
        # Процент от маржи
        if total_margin > 0:
            pnl_percentage = (total_pnl / total_margin) * 100
            print(f"📊 ROI портфеля: {pnl_percentage:+.2f}%")
        
        # Детализация по позициям
        if total_positions <= 10:  # Показываем детали только если позиций немного
            print(f"\\n{'Символ':^12} {'Сторона':^8} {'PnL':>12} {'%':>8} {'Маржа':>12}")
            print("─" * 60)
            
            # Сортируем по PnL
            sorted_positions = sorted(
                self.positions_data.items(),
                key=lambda x: x[1]['unrealizedPL'],
                reverse=True
            )
            
            for symbol, pos in sorted_positions:
                side_emoji = "📈" if pos['side'].lower() == 'long' else "📉"
                pnl_emoji = "🟢" if pos['unrealizedPL'] >= 0 else "🔴"
                
                print(f"{symbol:^12} {side_emoji}{pos['side'][:4]:^7} {pnl_emoji}${pos['unrealizedPL']:>10.2f} {pos['percentage']:>7.2f}% ${pos['margin']:>10.2f}")
        
        # Статистика производительности
        profitable_positions = sum(1 for pos in self.positions_data.values() if pos['unrealizedPL'] > 0)
        losing_positions = sum(1 for pos in self.positions_data.values() if pos['unrealizedPL'] < 0)
        
        print(f"\\n📈 Статистика:")
        print(f"🟢 Прибыльные: {profitable_positions}")
        print(f"🔴 Убыточные: {losing_positions}")
        
        if total_positions > 0:
            win_rate = (profitable_positions / total_positions) * 100
            print(f"🎯 Винрейт: {win_rate:.1f}%")
    
    def show_pnl_history(self, symbol, count=10):
        """Показать историю PnL для символа"""
        if symbol not in self.pnl_history or not self.pnl_history[symbol]:
            return
        
        history = self.pnl_history[symbol][-count:]
        
        print(f"\\n📈 ИСТОРИЯ PnL {symbol} (последние {len(history)}):")
        print(f"{'Время':^12} {'PnL':>12} {'%':>8} {'Цена':>12}")
        print("─" * 50)
        
        for entry in history:
            time_str = entry['timestamp'].strftime("%H:%M:%S")
            pnl_emoji = "🟢" if entry['pnl'] >= 0 else "🔴"
            print(f"{time_str:^12} {pnl_emoji}${entry['pnl']:>10.2f} {entry['percentage']:>7.2f}% ${entry['price']:>10.2f}")
    
    async def handle_message(self, message):
        """Обработка входящих сообщений"""
        try:
            data = json.loads(message)
            
            # Обработка ответа аутентификации
            if data.get('event') == 'login':
                if data.get('code') == '0':
                    print("✅ Аутентификация успешна!")
                    await self.subscribe_positions()
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
            
            # Обработка данных позиций
            elif data.get('action') in ['snapshot', 'update']:
                channel = data.get('arg', {}).get('channel', '')
                if channel == 'positions':
                    self.format_position_data(data)
            
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
            
            # Показываем историю для каждой позиции
            for symbol in self.pnl_history.keys():
                self.show_pnl_history(symbol)


async def monitor_all_positions():
    """Мониторинг всех позиций"""
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
        
        print("🔄 Мониторинг позиций...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        await positions_client.listen()
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await positions_client.disconnect()


async def pnl_tracker():
    """Трекер PnL с уведомлениями"""
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
    """Мониторинг рисков позиций"""
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
        
        print(f"🔄 Мониторинг рисков в течение {duration} секунд...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        try:
            await asyncio.wait_for(positions_client.listen(), timeout=duration)
        except asyncio.TimeoutError:
            print(f"\\n⏰ Мониторинг завершен ({duration} сек)")
            
            # Анализ рисков
            if positions_client.positions_data:
                print(f"\\n⚠️ АНАЛИЗ РИСКОВ:")
                
                high_leverage_positions = [
                    (symbol, pos) for symbol, pos in positions_client.positions_data.items()
                    if pos['leverage'] > 10
                ]
                
                large_loss_positions = [
                    (symbol, pos) for symbol, pos in positions_client.positions_data.items()
                    if pos['percentage'] < -10
                ]
                
                if high_leverage_positions:
                    print(f"🔴 Позиции с высоким плечом (>10x): {len(high_leverage_positions)}")
                    for symbol, pos in high_leverage_positions:
                        print(f"   {symbol}: {pos['leverage']:.0f}x")
                
                if large_loss_positions:
                    print(f"⚠️ Позиции с крупными убытками (>-10%): {len(large_loss_positions)}")
                    for symbol, pos in large_loss_positions:
                        print(f"   {symbol}: {pos['percentage']:.2f}%")
                
                if not high_leverage_positions and not large_loss_positions:
                    print("🟢 Рисковых позиций не обнаружено")
            else:
                print("📭 Нет открытых позиций для анализа")
        
    except KeyboardInterrupt:
        print("\\n👋 Мониторинг остановлен")
    finally:
        await positions_client.disconnect()


async def main():
    """Основная функция"""
    print("🎯 BITGET FUTURES POSITIONS CHANNEL")
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
