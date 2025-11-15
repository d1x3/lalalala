#!/bin/bash
# Скрипт для запуска бота поиска дешевых авиабилетов

echo "=================================================="
echo "  Запуск бота поиска дешевых авиабилетов"
echo "=================================================="
echo ""

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3."
    exit 1
fi

echo "✓ Python найден: $(python3 --version)"

# Проверяем наличие зависимостей
echo ""
echo "Проверка зависимостей..."

if ! python3 -c "import requests" 2>/dev/null; then
    echo "⚠️  Модуль 'requests' не найден. Установка..."
    pip3 install requests
fi

echo "✓ Все зависимости установлены"
echo ""

# Запускаем бота
echo "Запуск бота..."
echo ""

python3 cheap_flights_bot.py
