"""
Data Manager - управление входными данными для регистрации аккаунтов
"""

import json
import csv
import logging
from typing import Dict, List, Optional, Iterator
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AccountData:
    """Данные для регистрации одного аккаунта"""
    # Основные данные
    username: str
    password: str
    email: str
    phone: Optional[str] = None

    # Персональные данные
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None

    # Дополнительные данные
    country: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None

    # Служебные поля
    status: str = 'pending'  # pending, in_progress, success, failed
    error_message: Optional[str] = None
    created_at: Optional[str] = None

    # Пользовательские поля
    custom_data: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Конвертация в словарь"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'AccountData':
        """Создание из словаря"""
        return cls(**data)


class DataManager:
    """Менеджер для работы с данными регистрации"""

    def __init__(self, data_source: str):
        """
        Инициализация менеджера данных

        Args:
            data_source: Путь к файлу с данными (JSON, CSV, YAML)
        """
        self.data_source = Path(data_source)
        self.accounts: List[AccountData] = []
        self.current_index = 0

        if not self.data_source.exists():
            logger.warning(f"Файл данных не найден: {data_source}")
        else:
            self.load_data()

    def load_data(self):
        """Загрузка данных из файла"""
        logger.info(f"Загрузка данных из: {self.data_source}")

        suffix = self.data_source.suffix.lower()

        try:
            if suffix == '.json':
                self._load_json()
            elif suffix == '.csv':
                self._load_csv()
            elif suffix in ['.yml', '.yaml']:
                self._load_yaml()
            else:
                raise ValueError(f"Неподдерживаемый формат файла: {suffix}")

            logger.info(f"Загружено {len(self.accounts)} аккаунтов")
        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}")
            raise

    def _load_json(self):
        """Загрузка из JSON"""
        with open(self.data_source, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            self.accounts = [AccountData.from_dict(item) for item in data]
        elif isinstance(data, dict) and 'accounts' in data:
            self.accounts = [AccountData.from_dict(item) for item in data['accounts']]
        else:
            raise ValueError("Неверный формат JSON. Ожидается список или {accounts: [...]}")

    def _load_csv(self):
        """Загрузка из CSV"""
        with open(self.data_source, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.accounts = [AccountData.from_dict(row) for row in reader]

    def _load_yaml(self):
        """Загрузка из YAML"""
        with open(self.data_source, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if isinstance(data, list):
            self.accounts = [AccountData.from_dict(item) for item in data]
        elif isinstance(data, dict) and 'accounts' in data:
            self.accounts = [AccountData.from_dict(item) for item in data['accounts']]
        else:
            raise ValueError("Неверный формат YAML. Ожидается список или {accounts: [...]}")

    def save_data(self):
        """Сохранение данных в файл"""
        logger.info(f"Сохранение данных в: {self.data_source}")

        suffix = self.data_source.suffix.lower()

        try:
            if suffix == '.json':
                self._save_json()
            elif suffix == '.csv':
                self._save_csv()
            elif suffix in ['.yml', '.yaml']:
                self._save_yaml()

            logger.info("Данные сохранены успешно")
        except Exception as e:
            logger.error(f"Ошибка сохранения данных: {e}")
            raise

    def _save_json(self):
        """Сохранение в JSON"""
        with open(self.data_source, 'w', encoding='utf-8') as f:
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

        with open(self.data_source, 'w', encoding='utf-8', newline='') as f:
            fieldnames = self.accounts[0].to_dict().keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows([acc.to_dict() for acc in self.accounts])

    def _save_yaml(self):
        """Сохранение в YAML"""
        with open(self.data_source, 'w', encoding='utf-8') as f:
            yaml.dump(
                {'accounts': [acc.to_dict() for acc in self.accounts]},
                f,
                default_flow_style=False,
                allow_unicode=True
            )

    def get_next_account(self) -> Optional[AccountData]:
        """
        Получить следующий аккаунт для обработки

        Returns:
            AccountData или None если аккаунты закончились
        """
        pending_accounts = [acc for acc in self.accounts if acc.status == 'pending']

        if not pending_accounts:
            logger.info("Нет аккаунтов в статусе 'pending'")
            return None

        account = pending_accounts[0]
        account.status = 'in_progress'
        logger.info(f"Получен аккаунт для обработки: {account.username}")
        return account

    def update_account_status(self, account: AccountData, status: str,
                            error_message: Optional[str] = None):
        """
        Обновить статус аккаунта

        Args:
            account: Аккаунт для обновления
            status: Новый статус (success, failed)
            error_message: Сообщение об ошибке (если есть)
        """
        account.status = status
        account.error_message = error_message

        logger.info(f"Статус аккаунта {account.username} обновлен: {status}")

        # Автосохранение после обновления
        self.save_data()

    def get_statistics(self) -> Dict[str, int]:
        """
        Получить статистику по аккаунтам

        Returns:
            Словарь со статистикой
        """
        stats = {
            'total': len(self.accounts),
            'pending': 0,
            'in_progress': 0,
            'success': 0,
            'failed': 0
        }

        for account in self.accounts:
            if account.status in stats:
                stats[account.status] += 1

        return stats

    def get_accounts_by_status(self, status: str) -> List[AccountData]:
        """
        Получить список аккаунтов по статусу

        Args:
            status: Статус для фильтрации

        Returns:
            Список аккаунтов с указанным статусом
        """
        return [acc for acc in self.accounts if acc.status == status]

    def add_account(self, account: AccountData):
        """Добавить новый аккаунт"""
        self.accounts.append(account)
        logger.info(f"Добавлен новый аккаунт: {account.username}")

    def reset_failed_accounts(self):
        """Сбросить статус failed аккаунтов в pending"""
        count = 0
        for account in self.accounts:
            if account.status == 'failed':
                account.status = 'pending'
                account.error_message = None
                count += 1

        if count > 0:
            logger.info(f"Сброшено {count} аккаунтов из failed в pending")
            self.save_data()

    def iter_accounts(self, status: Optional[str] = None) -> Iterator[AccountData]:
        """
        Итератор по аккаунтам

        Args:
            status: Фильтр по статусу (если None - все аккаунты)

        Yields:
            AccountData
        """
        for account in self.accounts:
            if status is None or account.status == status:
                yield account


def create_sample_data_files():
    """Создание примеров файлов с данными"""

    # Пример данных
    sample_accounts = [
        {
            'username': 'user1',
            'password': 'SecurePass123!',
            'email': 'user1@example.com',
            'phone': '+1234567890',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-01',
            'country': 'USA',
            'city': 'New York',
            'status': 'pending'
        },
        {
            'username': 'user2',
            'password': 'AnotherPass456!',
            'email': 'user2@example.com',
            'phone': '+1234567891',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'date_of_birth': '1992-05-15',
            'country': 'USA',
            'city': 'Los Angeles',
            'status': 'pending'
        }
    ]

    # JSON
    with open('accounts_sample.json', 'w', encoding='utf-8') as f:
        json.dump({'accounts': sample_accounts}, f, indent=2, ensure_ascii=False)
    print("✓ Создан файл: accounts_sample.json")

    # CSV
    with open('accounts_sample.csv', 'w', encoding='utf-8', newline='') as f:
        fieldnames = sample_accounts[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_accounts)
    print("✓ Создан файл: accounts_sample.csv")

    # YAML
    with open('accounts_sample.yaml', 'w', encoding='utf-8') as f:
        yaml.dump({'accounts': sample_accounts}, f, default_flow_style=False, allow_unicode=True)
    print("✓ Создан файл: accounts_sample.yaml")


if __name__ == "__main__":
    # Создание примеров файлов
    create_sample_data_files()

    # Пример использования
    print("\n=== Пример использования DataManager ===\n")

    # Загрузка данных
    manager = DataManager('accounts_sample.json')

    # Статистика
    stats = manager.get_statistics()
    print(f"Статистика: {stats}")

    # Получение следующего аккаунта
    account = manager.get_next_account()
    if account:
        print(f"\nОбработка аккаунта: {account.username}")

        # Симуляция успешной регистрации
        manager.update_account_status(account, 'success')

    # Обновленная статистика
    stats = manager.get_statistics()
    print(f"\nОбновленная статистика: {stats}")
