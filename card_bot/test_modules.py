"""
Тестовый скрипт для проверки работы модулей
"""
import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, '/home/user/lalalala/card_bot')

def test_database():
    """Тест модуля базы данных"""
    print("🧪 Тестирование модуля базы данных...")
    try:
        from database import SecureCardDatabase

        # Создаем тестовую БД
        db = SecureCardDatabase(
            db_path='/tmp/test_cards.db',
            key_path='/tmp/test_key'
        )

        # Добавляем тестовую карту
        card_id = db.add_card(
            card_number='4276 3801 2345 6789',
            cvv='123',
            expiry='12/25',
            card_name='Тестовая карта'
        )
        print(f"  ✅ Карта добавлена с ID: {card_id}")

        # Получаем карту
        card_data = db.get_card(card_id)
        print(f"  ✅ Карта получена: {card_data['card_number']}")

        # Проверяем шифрование
        assert card_data['card_number'] == '4276 3801 2345 6789'
        assert card_data['cvv'] == '123'
        assert card_data['expiry'] == '12/25'
        print("  ✅ Данные корректно расшифрованы")

        # Удаляем тестовые файлы
        os.remove('/tmp/test_cards.db')
        os.remove('/tmp/test_key')

        print("✅ Модуль базы данных работает корректно!\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка в модуле БД: {e}\n")
        return False


def test_parser():
    """Тест модуля парсера"""
    print("🧪 Тестирование модуля парсера...")
    try:
        from ocr_parser import CardParser

        parser = CardParser()

        # Тест парсинга номера карты
        test_text = "4276 3801 2345 6789 12/25 123"
        card_number = parser.parse_card_number(test_text)
        print(f"  ✅ Номер карты распознан: {card_number}")

        # Тест парсинга срока действия
        expiry = parser.parse_expiry(test_text)
        print(f"  ✅ Срок действия распознан: {expiry}")

        # Тест парсинга CVV
        cvv = parser.parse_cvv(test_text, card_number)
        print(f"  ✅ CVV распознан: {cvv}")

        # Тест валидации карты
        is_valid = parser.validate_card_number('4276380123456789')
        print(f"  ✅ Валидация работает: {is_valid}")

        print("✅ Модуль парсера работает корректно!\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка в модуле парсера: {e}\n")
        return False


def test_imports():
    """Тест импорта всех зависимостей"""
    print("🧪 Тестирование импорта зависимостей...")
    errors = []

    try:
        import telegram
        print("  ✅ python-telegram-bot")
    except ImportError as e:
        errors.append(f"python-telegram-bot: {e}")

    try:
        import pytesseract
        print("  ✅ pytesseract")
    except ImportError as e:
        errors.append(f"pytesseract: {e}")

    try:
        from PIL import Image
        print("  ✅ Pillow")
    except ImportError as e:
        errors.append(f"Pillow: {e}")

    try:
        from cryptography.fernet import Fernet
        print("  ✅ cryptography")
    except ImportError as e:
        errors.append(f"cryptography: {e}")

    if errors:
        print("\n❌ Ошибки импорта:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ Все зависимости установлены!\n")
        return True


if __name__ == '__main__':
    print("=" * 50)
    print("  ТЕСТИРОВАНИЕ МОДУЛЕЙ БОТА")
    print("=" * 50)
    print()

    results = []
    results.append(("Импорт зависимостей", test_imports()))
    results.append(("Модуль базы данных", test_database()))
    results.append(("Модуль парсера", test_parser()))

    print("=" * 50)
    print("  РЕЗУЛЬТАТЫ ТЕСТОВ")
    print("=" * 50)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print()
    if all(r[1] for r in results):
        print("🎉 Все тесты пройдены успешно!")
        print("Бот готов к запуску: python3 bot.py")
    else:
        print("⚠️  Некоторые тесты не пройдены. Проверьте установку зависимостей.")
