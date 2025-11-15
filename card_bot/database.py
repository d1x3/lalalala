"""
Модуль для работы с зашифрованной базой данных банковских карт
"""
import sqlite3
import json
from cryptography.fernet import Fernet
from pathlib import Path
import os


class SecureCardDatabase:
    """Класс для безопасного хранения данных банковских карт"""

    def __init__(self, db_path: str = "cards.db", key_path: str = ".encryption_key"):
        self.db_path = db_path
        self.key_path = key_path
        self.cipher = self._load_or_create_key()
        self._init_db()

    def _load_or_create_key(self) -> Fernet:
        """Загружает или создает ключ шифрования"""
        if os.path.exists(self.key_path):
            with open(self.key_path, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_path, 'wb') as f:
                f.write(key)
            # Устанавливаем права доступа только для владельца
            os.chmod(self.key_path, 0o600)

        return Fernet(key)

    def _init_db(self):
        """Инициализирует базу данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_name TEXT,
                    encrypted_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def _encrypt_data(self, data: dict) -> str:
        """Шифрует данные карты"""
        json_data = json.dumps(data)
        encrypted = self.cipher.encrypt(json_data.encode())
        return encrypted.decode()

    def _decrypt_data(self, encrypted_data: str) -> dict:
        """Дешифрует данные карты"""
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return json.loads(decrypted.decode())

    def add_card(self, card_number: str, cvv: str, expiry: str, card_name: str = None):
        """
        Добавляет карту в базу данных

        Args:
            card_number: номер карты
            cvv: CVV код
            expiry: срок действия (MM/YY)
            card_name: название карты (опционально)

        Returns:
            id добавленной карты
        """
        data = {
            'card_number': card_number,
            'cvv': cvv,
            'expiry': expiry
        }

        encrypted = self._encrypt_data(data)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO cards (card_name, encrypted_data) VALUES (?, ?)',
                (card_name, encrypted)
            )
            conn.commit()
            return cursor.lastrowid

    def get_all_cards(self):
        """Получает список всех карт (без расшифровки)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, card_name, created_at FROM cards ORDER BY id')
            return cursor.fetchall()

    def card_exists(self, card_number: str) -> bool:
        """
        Проверяет, существует ли карта с таким номером

        Args:
            card_number: номер карты для проверки

        Returns:
            True если карта уже есть в БД
        """
        # Убираем пробелы из номера для сравнения
        clean_number = card_number.replace(' ', '')

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT encrypted_data FROM cards')
            all_cards = cursor.fetchall()

            for (encrypted_data,) in all_cards:
                card_data = self._decrypt_data(encrypted_data)
                stored_number = card_data.get('card_number', '').replace(' ', '')
                if stored_number == clean_number:
                    return True

        return False

    def get_card(self, card_id: int):
        """
        Получает данные карты по ID

        Args:
            card_id: ID карты

        Returns:
            dict с данными карты или None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT encrypted_data FROM cards WHERE id = ?', (card_id,))
            result = cursor.fetchone()

            if result:
                return self._decrypt_data(result[0])
            return None

    def delete_card(self, card_id: int) -> bool:
        """
        Удаляет карту по ID

        Args:
            card_id: ID карты

        Returns:
            True если карта удалена, False если не найдена
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cards WHERE id = ?', (card_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_card_name(self, card_id: int, new_name: str) -> bool:
        """
        Обновляет название карты

        Args:
            card_id: ID карты
            new_name: новое название

        Returns:
            True если обновлено, False если карта не найдена
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE cards SET card_name = ? WHERE id = ?',
                (new_name, card_id)
            )
            conn.commit()
            return cursor.rowcount > 0
