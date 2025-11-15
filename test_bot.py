#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы бота
"""

import sys

print("=" * 60)
print("Тестирование бота поиска авиабилетов")
print("=" * 60)

# Проверка импортов
print("\n1. Проверка зависимостей...")
try:
    import requests
    print("   ✓ requests")
except ImportError:
    print("   ✗ requests не установлен")
    print("   Установите: pip3 install requests")
    sys.exit(1)

try:
    import json
    print("   ✓ json")
except ImportError:
    print("   ✗ json не установлен")
    sys.exit(1)

try:
    from datetime import datetime
    print("   ✓ datetime")
except ImportError:
    print("   ✗ datetime не установлен")
    sys.exit(1)

# Проверка модулей бота
print("\n2. Проверка модулей бота...")
try:
    import flight_config as config
    print("   ✓ flight_config")
except ImportError as e:
    print(f"   ✗ flight_config: {e}")
    sys.exit(1)

try:
    from flight_finder import FlightFinder
    print("   ✓ flight_finder")
except ImportError as e:
    print(f"   ✗ flight_finder: {e}")
    sys.exit(1)

try:
    from telegram_notifier import TelegramNotifier
    print("   ✓ telegram_notifier")
except ImportError as e:
    print(f"   ✗ telegram_notifier: {e}")
    sys.exit(1)

# Проверка конфигурации
print("\n3. Проверка конфигурации...")
print(f"   Маршрут: {config.ORIGIN_CITY} → {config.DESTINATION_CITY}")
print(f"   Макс. цена: {config.MAX_PRICE} ₽")
print(f"   Даты поиска: {len(config.DEPARTURE_DATES)} дат(ы)")
print(f"   Интервал: {config.CHECK_INTERVAL} сек ({config.CHECK_INTERVAL // 60} мин)")

# Проверка Telegram API
print("\n4. Проверка подключения к Telegram...")
telegram = TelegramNotifier(config.TELEGRAM_BOT_TOKEN)
if telegram.test_connection():
    print("   ✓ Подключение к Telegram успешно")
else:
    print("   ✗ Ошибка подключения к Telegram")
    print("   Проверьте токен бота в flight_config.py")
    sys.exit(1)

# Проверка chat_id
print("\n5. Проверка chat_id...")
chat_id = telegram.get_chat_id()
if chat_id:
    print(f"   ✓ Chat ID найден: {chat_id}")
    print("   Бот готов к отправке уведомлений")
else:
    print("   ⚠ Chat ID не найден")
    print("   Отправьте /start боту в Telegram, затем запустите бота снова")

print("\n" + "=" * 60)
print("✓ Все тесты пройдены! Бот готов к запуску.")
print("=" * 60)
print("\nДля запуска бота используйте:")
print("  python3 cheap_flights_bot.py --once    (однократный поиск)")
print("  python3 cheap_flights_bot.py           (непрерывная работа)")
print("  ./start_flight_bot.sh                  (через скрипт)")
print()
