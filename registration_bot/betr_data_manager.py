"""
Betr Data Manager - управление данными для регистрации на Betr
"""

import json
import csv
import logging
import random
import string
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BetrAccountData:
    """Данные для регистрации аккаунта на Betr"""
    # Персональные данные (из вашей таблицы)
    first_name: str
    last_name: str
    date_of_birth: str  # Формат: YYYY-MM-DD или MM/DD/YYYY
    address: str  # Полный адрес
    ssn_last4: str  # Последние 4 цифры SSN

    # Генерируемые данные
    email: str = ""
    password: str = ""
    phone: str = ""

    # Данные из DaisySMS
    daisy_activation_id: Optional[str] = None
    daisy_phone: Optional[str] = None
    daisy_sms_code: Optional[str] = None

    # Статус регистрации
    status: str = "pending"  # pending, in_progress, success, failed, verified
    error_message: Optional[str] = None
    registered_at: Optional[str] = None

    # Дополнительные данные
    profile_id: Optional[str] = None  # ID профиля анти-детект браузера
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        """Конвертация в словарь"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'BetrAccountData':
        """Создание из словаря"""
        # Убираем поля которых может не быть
        valid_fields = {k: v for k, v in data.items() if k in cls.__annotations__}
        return cls(**valid_fields)

    def parse_date_of_birth(self) -> Dict[str, str]:
        """
        Разбить дату рождения на компоненты

        Returns:
            {"year": "1990", "month": "03", "day": "15"}
        """
        # Поддержка форматов: YYYY-MM-DD, MM/DD/YYYY, DD.MM.YYYY
        date_str = self.date_of_birth.replace('/', '-').replace('.', '-')
        parts = date_str.split('-')

        if len(parts) != 3:
            logger.error(f"Неверный формат даты: {self.date_of_birth}")
            return {"year": "", "month": "", "day": ""}

        # Определяем формат
        if len(parts[0]) == 4:  # YYYY-MM-DD
            year, month, day = parts
        else:  # MM-DD-YYYY или DD-MM-YYYY
            # Предполагаем MM-DD-YYYY
            month, day, year = parts

        return {
            "year": year,
            "month": month.zfill(2),  # Добавляем ведущий 0 если нужно
            "day": day.zfill(2)
        }


class BetrDataManager:
    """Менеджер данных для Betr регистраций"""

    def __init__(self, data_file: str = "betr_accounts.json"):
        """
        Инициализация менеджера

        Args:
            data_file: Путь к файлу с данными
        """
        self.data_file = Path(data_file)
        self.accounts: List[BetrAccountData] = []

        if self.data_file.exists():
            self.load_data()
        else:
            logger.warning(f"Файл данных не найден: {data_file}")

    def load_data(self):
        """Загрузка данных из файла"""
        logger.info(f"Загрузка данных из: {self.data_file}")

        suffix = self.data_file.suffix.lower()

        try:
            if suffix == '.json':
                self._load_json()
            elif suffix == '.csv':
                self._load_csv()
            else:
                raise ValueError(f"Неподдерживаемый формат: {suffix}")

            logger.info(f"Загружено {len(self.accounts)} аккаунтов")

        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}")
            raise

    def _load_json(self):
        """Загрузка из JSON"""
        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            self.accounts = [BetrAccountData.from_dict(item) for item in data]
        elif isinstance(data, dict) and 'accounts' in data:
            self.accounts = [BetrAccountData.from_dict(item) for item in data['accounts']]

    def _load_csv(self):
        """Загрузка из CSV"""
        with open(self.data_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.accounts = [BetrAccountData.from_dict(row) for row in reader]

    def save_data(self):
        """Сохранение данных в файл"""
        logger.info(f"Сохранение данных в: {self.data_file}")

        suffix = self.data_file.suffix.lower()

        try:
            if suffix == '.json':
                self._save_json()
            elif suffix == '.csv':
                self._save_csv()

            logger.info("Данные сохранены")

        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
            raise

    def _save_json(self):
        """Сохранение в JSON"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(
                {'accounts': [acc.to_dict() for acc in self.accounts]},
                f,
                indent=2,
                ensure_ascii=False
            )

    def _save_csv(self):
        """Сохранение в CSV"""
        if not self.accounts:
            return

        with open(self.data_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = self.accounts[0].to_dict().keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows([acc.to_dict() for acc in self.accounts])

    @staticmethod
    def generate_email(first_name: str, last_name: str, domain: str = "gmail.com") -> str:
        """
        Генерация email адреса

        Args:
            first_name: Имя
            last_name: Фамилия
            domain: Домен email

        Returns:
            Email адрес
        """
        # Создаем уникальный email
        random_suffix = ''.join(random.choices(string.digits, k=4))
        email = f"{first_name.lower()}.{last_name.lower()}{random_suffix}@{domain}"
        return email

    @staticmethod
    def generate_password(length: int = 12) -> str:
        """
        Генерация надежного пароля

        Args:
            length: Длина пароля

        Returns:
            Пароль
        """
        # Минимум: 1 заглавная, 1 строчная, 1 цифра, 1 спецсимвол
        uppercase = random.choice(string.ascii_uppercase)
        lowercase = random.choice(string.ascii_lowercase)
        digit = random.choice(string.digits)
        special = random.choice('!@#$%^&*')

        # Остальные символы
        remaining = length - 4
        all_chars = string.ascii_letters + string.digits + '!@#$%^&*'
        other = ''.join(random.choices(all_chars, k=remaining))

        # Перемешиваем
        password = list(uppercase + lowercase + digit + special + other)
        random.shuffle(password)

        return ''.join(password)

    def prepare_account(self, account: BetrAccountData):
        """
        Подготовить аккаунт к регистрации (сгенерировать email и пароль)

        Args:
            account: Аккаунт для подготовки
        """
        if not account.email:
            account.email = self.generate_email(account.first_name, account.last_name)
            logger.info(f"Сгенерирован email: {account.email}")

        if not account.password:
            account.password = self.generate_password()
            logger.info(f"Сгенерирован пароль для {account.email}")

    def get_next_account(self) -> Optional[BetrAccountData]:
        """
        Получить следующий аккаунт для обработки

        Returns:
            BetrAccountData или None
        """
        pending = [acc for acc in self.accounts if acc.status == 'pending']

        if not pending:
            logger.info("Нет аккаунтов в статусе pending")
            return None

        account = pending[0]
        account.status = 'in_progress'

        # Подготовка аккаунта
        self.prepare_account(account)

        logger.info(f"Получен аккаунт: {account.first_name} {account.last_name}")
        return account

    def update_account_status(self, account: BetrAccountData, status: str,
                            error_message: Optional[str] = None):
        """
        Обновить статус аккаунта

        Args:
            account: Аккаунт
            status: Новый статус
            error_message: Сообщение об ошибке (опционально)
        """
        account.status = status
        account.error_message = error_message

        if status == 'success':
            account.registered_at = datetime.now().isoformat()

        logger.info(f"Статус {account.email}: {status}")
        self.save_data()

    def get_statistics(self) -> Dict[str, int]:
        """
        Получить статистику

        Returns:
            Словарь со статистикой
        """
        stats = {
            'total': len(self.accounts),
            'pending': 0,
            'in_progress': 0,
            'success': 0,
            'failed': 0,
            'verified': 0
        }

        for account in self.accounts:
            if account.status in stats:
                stats[account.status] += 1

        return stats

    def reset_failed_accounts(self):
        """Сбросить failed аккаунты в pending"""
        count = 0
        for account in self.accounts:
            if account.status == 'failed':
                account.status = 'pending'
                account.error_message = None
                account.daisy_activation_id = None
                account.daisy_phone = None
                account.daisy_sms_code = None
                count += 1

        if count > 0:
            logger.info(f"Сброшено {count} аккаунтов из failed в pending")
            self.save_data()


def create_sample_betr_data():
    """Создание примера файла с данными для Betr"""
    sample_accounts = [
        {
            "first_name": "John",
            "last_name": "Smith",
            "date_of_birth": "1990-03-15",
            "address": "123 Main St, New York, NY 10001",
            "ssn_last4": "1234",
            "status": "pending"
        },
        {
            "first_name": "Sarah",
            "last_name": "Johnson",
            "date_of_birth": "1985-07-22",
            "address": "456 Oak Ave, Los Angeles, CA 90001",
            "ssn_last4": "5678",
            "status": "pending"
        },
        {
            "first_name": "Michael",
            "last_name": "Williams",
            "date_of_birth": "1992-11-08",
            "address": "789 Pine Rd, Chicago, IL 60601",
            "ssn_last4": "9012",
            "status": "pending"
        }
    ]

    # Сохраняем в JSON
    with open('betr_accounts.json', 'w', encoding='utf-8') as f:
        json.dump({'accounts': sample_accounts}, f, indent=2)
    print("✓ Создан файл: betr_accounts.json")

    # Сохраняем в CSV
    with open('betr_accounts.csv', 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['first_name', 'last_name', 'date_of_birth', 'address',
                     'ssn_last4', 'email', 'password', 'phone', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for acc in sample_accounts:
            acc.update({'email': '', 'password': '', 'phone': ''})
            writer.writerow(acc)
    print("✓ Создан файл: betr_accounts.csv")


if __name__ == "__main__":
    print("=== Betr Data Manager ===\n")

    # Создание примеров
    create_sample_betr_data()

    # Тест менеджера
    print("\nТестирование менеджера:")
    manager = BetrDataManager('betr_accounts.json')

    # Получение аккаунта
    account = manager.get_next_account()
    if account:
        print(f"\nПолучен аккаунт:")
        print(f"  Имя: {account.first_name} {account.last_name}")
        print(f"  Email: {account.email}")
        print(f"  Пароль: {account.password}")
        print(f"  Дата рождения: {account.date_of_birth}")
        print(f"  Адрес: {account.address}")
        print(f"  SSN (last 4): {account.ssn_last4}")

        # Разбор даты
        dob = account.parse_date_of_birth()
        print(f"  Дата (разобрано): {dob['month']}/{dob['day']}/{dob['year']}")

    # Статистика
    stats = manager.get_statistics()
    print(f"\nСтатистика: {stats}")
