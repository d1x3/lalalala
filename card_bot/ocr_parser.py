"""
Модуль для OCR и парсинга данных банковских карт
"""
import re
from PIL import Image
import pytesseract
from io import BytesIO


class CardParser:
    """Класс для распознавания и парсинга данных карт с изображений"""

    # Паттерны для поиска данных карты
    CARD_NUMBER_PATTERN = r'\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b'
    CVV_PATTERN = r'\b(\d{3,4})\b'
    EXPIRY_PATTERN = r'\b(0[1-9]|1[0-2])[/\-\s]?(\d{2})\b'

    @staticmethod
    def preprocess_image(image_bytes: bytes) -> Image.Image:
        """
        Предобработка изображения для улучшения OCR

        Args:
            image_bytes: байты изображения

        Returns:
            PIL Image объект
        """
        image = Image.open(BytesIO(image_bytes))

        # Конвертируем в RGB если нужно
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Увеличиваем контраст и размер для лучшего распознавания
        # Увеличиваем изображение в 2 раза
        width, height = image.size
        image = image.resize((width * 2, height * 2), Image.Resampling.LANCZOS)

        return image

    @staticmethod
    def extract_text_from_image(image_bytes: bytes) -> str:
        """
        Извлекает текст из изображения с помощью OCR

        Args:
            image_bytes: байты изображения

        Returns:
            распознанный текст
        """
        image = CardParser.preprocess_image(image_bytes)

        # Tesseract OCR с параметрами для цифр
        # --psm 6: предполагаем единый блок текста
        # -c tessedit_char_whitelist: разрешаем только нужные символы
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789/-'
        text = pytesseract.image_to_string(image, config=custom_config, lang='eng')

        return text

    @staticmethod
    def parse_card_number(text: str) -> str:
        """
        Извлекает номер карты из текста

        Args:
            text: текст для парсинга

        Returns:
            номер карты или None
        """
        # Удаляем все пробелы и дефисы для поиска
        clean_text = re.sub(r'[\s\-]', '', text)

        # Ищем последовательность из 16 цифр
        matches = re.findall(r'\b\d{16}\b', clean_text)

        if matches:
            # Форматируем номер карты с пробелами
            card_number = matches[0]
            return f"{card_number[0:4]} {card_number[4:8]} {card_number[8:12]} {card_number[12:16]}"

        # Пробуем найти с разделителями
        matches = re.findall(CardParser.CARD_NUMBER_PATTERN, text)
        if matches:
            return re.sub(r'[\s\-]', '', matches[0])

        return None

    @staticmethod
    def parse_expiry(text: str) -> str:
        """
        Извлекает срок действия из текста

        Args:
            text: текст для парсинга

        Returns:
            срок действия в формате MM/YY или None
        """
        matches = re.findall(CardParser.EXPIRY_PATTERN, text)

        if matches:
            month, year = matches[0]
            return f"{month}/{year}"

        return None

    @staticmethod
    def parse_cvv(text: str, card_number: str = None) -> str:
        """
        Извлекает CVV код из текста

        Args:
            text: текст для парсинга
            card_number: номер карты (для исключения из поиска)

        Returns:
            CVV код или None
        """
        # Удаляем номер карты из текста, если он есть
        if card_number:
            text = text.replace(card_number.replace(' ', ''), '')

        # Ищем 3-4 цифры
        matches = re.findall(CardParser.CVV_PATTERN, text)

        # Фильтруем: CVV это 3 или 4 цифры, но не часть номера карты
        for match in matches:
            if len(match) == 3 or len(match) == 4:
                # Проверяем что это не часть даты
                if not re.search(rf'\d{{2}}[/\-\s]?{match}', text):
                    return match

        return None

    @classmethod
    def parse_card_from_image(cls, image_bytes: bytes) -> dict:
        """
        Полный парсинг карты из изображения

        Args:
            image_bytes: байты изображения

        Returns:
            dict с данными карты: {card_number, cvv, expiry}
        """
        # Извлекаем текст
        text = cls.extract_text_from_image(image_bytes)

        # Парсим данные
        card_number = cls.parse_card_number(text)
        expiry = cls.parse_expiry(text)
        cvv = cls.parse_cvv(text, card_number)

        return {
            'card_number': card_number,
            'cvv': cvv,
            'expiry': expiry,
            'raw_text': text  # для отладки
        }

    @staticmethod
    def format_card_number(card_number: str) -> str:
        """
        Форматирует номер карты с пробелами

        Args:
            card_number: номер карты

        Returns:
            отформатированный номер
        """
        # Удаляем все не-цифры
        clean = re.sub(r'\D', '', card_number)

        if len(clean) == 16:
            return f"{clean[0:4]} {clean[4:8]} {clean[8:12]} {clean[12:16]}"

        return card_number

    @staticmethod
    def validate_card_number(card_number: str) -> bool:
        """
        Проверяет номер карты по алгоритму Луна

        Args:
            card_number: номер карты

        Returns:
            True если валиден
        """
        # Удаляем все не-цифры
        clean = re.sub(r'\D', '', card_number)

        if len(clean) != 16:
            return False

        # Алгоритм Луна
        digits = [int(d) for d in clean]
        checksum = 0

        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit

        return checksum % 10 == 0
