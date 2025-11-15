#!/usr/bin/env python3
"""
Тестовый запуск бота - проверка отправки уведомлений в Telegram
"""

import sys
sys.path.insert(0, '/home/user/lalalala')

from telegram_notifier import TelegramNotifier
from flight_finder import format_flight_message
import flight_config as config

print("=" * 60)
print("ТЕСТ: Проверка отправки уведомлений в Telegram")
print("=" * 60)

# Создаем тестовый билет
test_flight = {
    'origin': 'MOW',
    'destination': 'UFA',
    'departure_date': '2024-12-26T19:30:00',
    'price': 8500,
    'currency': 'RUB',
    'airline': 'Аэрофлот',
    'transfers': 0,
    'link': 'https://www.aviasales.ru/search/MOW2024-12-26UFA1'
}

print("\nТестовый билет:")
print(f"  Маршрут: {test_flight['origin']} → {test_flight['destination']}")
print(f"  Дата: {test_flight['departure_date']}")
print(f"  Цена: {test_flight['price']} ₽")
print(f"  Авиакомпания: {test_flight['airline']}")
print()

# Инициализируем Telegram notifier
telegram = TelegramNotifier(config.TELEGRAM_BOT_TOKEN)

# Проверяем подключение
print("Проверка подключения к Telegram API...")
if telegram.test_connection():
    print("✓ Подключение успешно!")
else:
    print("✗ Ошибка подключения к Telegram")
    sys.exit(1)

# Получаем chat_id
print("\nПоиск chat_id...")
chat_id = telegram.get_chat_id()
if chat_id:
    print(f"✓ Chat ID найден: {chat_id}")
else:
    print("⚠ Chat ID не найден")
    print("Отправьте /start боту @umartaufabot в Telegram")
    print("\nПопытка отправки без chat_id (бот попробует определить автоматически)...")

# Форматируем сообщение
message = format_flight_message(test_flight)

print("\n" + "=" * 60)
print("Сообщение для отправки:")
print("=" * 60)
print(message)
print("=" * 60)

# Отправляем тестовое уведомление
print("\nОтправка уведомления в Telegram...")
if telegram.send_message(message, chat_id):
    print("✓ Уведомление успешно отправлено!")
    print("\nПроверьте Telegram - вы должны получить сообщение от бота @umartaufabot")
else:
    print("✗ Ошибка отправки уведомления")
    print("\nВозможные причины:")
    print("  1. Вы не отправили /start боту @umartaufabot")
    print("  2. Неверный токен бота")
    print("  3. Проблемы с сетью")

print("\n" + "=" * 60)
print("Тест завершен")
print("=" * 60)
