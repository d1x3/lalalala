#!/bin/bash

echo "🚀 Запуск бота для хранения банковских карт..."
echo ""

# Проверка установки tesseract
if ! command -v tesseract &> /dev/null; then
    echo "❌ Tesseract OCR не найден!"
    echo "Установите его командой:"
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-eng"
    echo "  macOS: brew install tesseract"
    exit 1
fi

echo "✅ Tesseract OCR установлен"

# Проверка Python зависимостей
if ! python3 -c "import telegram" 2>/dev/null; then
    echo "⚠️  Python зависимости не установлены"
    echo "Устанавливаю зависимости..."
    pip install -r requirements.txt
fi

echo "✅ Все зависимости установлены"
echo ""
echo "🤖 Запускаю бота..."
echo ""

# Запуск бота
python3 bot.py
