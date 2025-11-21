"""
SMS Service - модуль для получения SMS кодов через различные сервисы
Поддерживает интеграцию с популярными SMS-сервисами
"""

import requests
import time
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SMSServiceType(Enum):
    """Типы поддерживаемых SMS сервисов"""
    SMS_ACTIVATE = "sms_activate"
    FIVE_SIM = "5sim"
    TEMP_MAIL = "temp_mail"
    CUSTOM = "custom"


class BaseSMSService(ABC):
    """Базовый класс для SMS сервисов"""

    def __init__(self, api_key: str):
        """
        Инициализация сервиса

        Args:
            api_key: API ключ сервиса
        """
        self.api_key = api_key
        self.session = requests.Session()

    @abstractmethod
    def get_number(self, service: str, country: str = "ru") -> Optional[Dict[str, Any]]:
        """
        Получить номер телефона

        Args:
            service: Название сервиса (например, "google", "telegram")
            country: Код страны

        Returns:
            Словарь с информацией о номере: {"id": "123", "phone": "+79001234567"}
        """
        pass

    @abstractmethod
    def get_sms_code(self, activation_id: str, timeout: int = 300) -> Optional[str]:
        """
        Получить SMS код

        Args:
            activation_id: ID активации
            timeout: Таймаут ожидания SMS

        Returns:
            SMS код или None
        """
        pass

    @abstractmethod
    def cancel_activation(self, activation_id: str) -> bool:
        """
        Отменить активацию

        Args:
            activation_id: ID активации

        Returns:
            True если успешно
        """
        pass


class SMSActivateService(BaseSMSService):
    """Сервис sms-activate.org"""

    BASE_URL = "https://api.sms-activate.org/stubs/handler_api.php"

    def __init__(self, api_key: str):
        super().__init__(api_key)
        logger.info("Инициализирован сервис SMS-Activate")

    def _make_request(self, params: Dict[str, Any]) -> str:
        """Выполнить запрос к API"""
        params['api_key'] = self.api_key

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            return response.text.strip()

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к SMS-Activate: {e}")
            return ""

    def get_number(self, service: str, country: str = "ru") -> Optional[Dict[str, Any]]:
        """
        Получить номер телефона

        Args:
            service: Код сервиса (например, "go" для Google)
            country: Код страны (по умолчанию "ru")

        Returns:
            {"id": "activation_id", "phone": "+79001234567"}
        """
        params = {
            'action': 'getNumber',
            'service': service,
            'country': country.lower()
        }

        response = self._make_request(params)

        if response.startswith('ACCESS_NUMBER'):
            # Формат: ACCESS_NUMBER:activation_id:phone_number
            parts = response.split(':')
            if len(parts) == 3:
                activation_id = parts[1]
                phone = parts[2]

                logger.info(f"Получен номер: {phone} (ID: {activation_id})")
                return {
                    'id': activation_id,
                    'phone': phone
                }

        logger.error(f"Не удалось получить номер: {response}")
        return None

    def get_sms_code(self, activation_id: str, timeout: int = 300) -> Optional[str]:
        """
        Получить SMS код

        Args:
            activation_id: ID активации
            timeout: Таймаут ожидания в секундах

        Returns:
            SMS код
        """
        logger.info(f"Ожидание SMS кода для активации {activation_id}...")

        start_time = time.time()
        check_interval = 5  # Интервал проверки в секундах

        while time.time() - start_time < timeout:
            params = {
                'action': 'getStatus',
                'id': activation_id
            }

            response = self._make_request(params)

            if response.startswith('STATUS_OK'):
                # Формат: STATUS_OK:code
                code = response.split(':')[1]
                logger.info(f"Получен SMS код: {code}")
                return code

            elif response == 'STATUS_WAIT_CODE':
                # Ожидаем SMS
                time.sleep(check_interval)

            elif response == 'STATUS_CANCEL':
                logger.warning("Активация отменена")
                return None

            else:
                logger.warning(f"Неожиданный статус: {response}")
                time.sleep(check_interval)

        logger.error(f"Таймаут ожидания SMS (активация: {activation_id})")
        return None

    def cancel_activation(self, activation_id: str) -> bool:
        """Отменить активацию"""
        params = {
            'action': 'setStatus',
            'id': activation_id,
            'status': '8'  # 8 = отмена
        }

        response = self._make_request(params)

        if response == 'ACCESS_CANCEL':
            logger.info(f"Активация {activation_id} отменена")
            return True

        logger.error(f"Не удалось отменить активацию: {response}")
        return False

    def confirm_sms_received(self, activation_id: str) -> bool:
        """Подтвердить получение SMS"""
        params = {
            'action': 'setStatus',
            'id': activation_id,
            'status': '6'  # 6 = завершить успешно
        }

        response = self._make_request(params)

        if response == 'ACCESS_ACTIVATION':
            logger.info(f"Активация {activation_id} завершена успешно")
            return True

        return False


class FiveSimService(BaseSMSService):
    """Сервис 5sim.net"""

    BASE_URL = "https://5sim.net/v1"

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        })
        logger.info("Инициализирован сервис 5sim")

    def get_number(self, service: str, country: str = "russia") -> Optional[Dict[str, Any]]:
        """Получить номер от 5sim"""
        url = f"{self.BASE_URL}/user/buy/activation/{country}/any/{service}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            activation_id = str(data['id'])
            phone = data['phone']

            logger.info(f"Получен номер: {phone} (ID: {activation_id})")
            return {
                'id': activation_id,
                'phone': phone
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения номера от 5sim: {e}")
            return None

    def get_sms_code(self, activation_id: str, timeout: int = 300) -> Optional[str]:
        """Получить SMS код от 5sim"""
        logger.info(f"Ожидание SMS кода для активации {activation_id}...")

        url = f"{self.BASE_URL}/user/check/{activation_id}"
        start_time = time.time()
        check_interval = 5

        while time.time() - start_time < timeout:
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()

                if data.get('sms'):
                    code = data['sms'][0]['code']
                    logger.info(f"Получен SMS код: {code}")
                    return code

                time.sleep(check_interval)

            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка проверки SMS: {e}")
                time.sleep(check_interval)

        logger.error(f"Таймаут ожидания SMS (активация: {activation_id})")
        return None

    def cancel_activation(self, activation_id: str) -> bool:
        """Отменить активацию в 5sim"""
        url = f"{self.BASE_URL}/user/cancel/{activation_id}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            logger.info(f"Активация {activation_id} отменена")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка отмены активации: {e}")
            return False


class TempMailService:
    """Сервис для временной электронной почты"""

    BASE_URL = "https://api.tempmail.lol"

    def __init__(self):
        self.session = requests.Session()
        logger.info("Инициализирован сервис TempMail")

    def create_email(self) -> Optional[Dict[str, str]]:
        """
        Создать временный email

        Returns:
            {"email": "random@tempmail.lol", "token": "..."}
        """
        url = f"{self.BASE_URL}/generate"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            email = data['address']
            token = data['token']

            logger.info(f"Создан временный email: {email}")
            return {
                'email': email,
                'token': token
            }

        except Exception as e:
            logger.error(f"Ошибка создания email: {e}")
            return None

    def get_messages(self, email: str, timeout: int = 300) -> Optional[list]:
        """
        Получить сообщения

        Args:
            email: Адрес email
            timeout: Таймаут ожидания

        Returns:
            Список сообщений
        """
        logger.info(f"Ожидание сообщений для {email}...")

        url = f"{self.BASE_URL}/auth/{email}"
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()

                if data.get('email'):
                    messages = data['email']
                    if messages:
                        logger.info(f"Получено {len(messages)} сообщений")
                        return messages

                time.sleep(5)

            except Exception as e:
                logger.error(f"Ошибка проверки почты: {e}")
                time.sleep(5)

        logger.error(f"Таймаут ожидания сообщений для {email}")
        return None


class SMSServiceManager:
    """Менеджер для работы с разными SMS сервисами"""

    def __init__(self, service_type: SMSServiceType, api_key: Optional[str] = None):
        """
        Инициализация менеджера

        Args:
            service_type: Тип сервиса
            api_key: API ключ (если требуется)
        """
        self.service_type = service_type
        self.service = self._init_service(service_type, api_key)

    def _init_service(self, service_type: SMSServiceType,
                     api_key: Optional[str]) -> BaseSMSService:
        """Инициализация конкретного сервиса"""
        if service_type == SMSServiceType.SMS_ACTIVATE:
            if not api_key:
                raise ValueError("API ключ обязателен для SMS-Activate")
            return SMSActivateService(api_key)

        elif service_type == SMSServiceType.FIVE_SIM:
            if not api_key:
                raise ValueError("API ключ обязателен для 5sim")
            return FiveSimService(api_key)

        else:
            raise ValueError(f"Неподдерживаемый тип сервиса: {service_type}")

    def get_phone_and_code(self, service: str, country: str = "ru",
                          timeout: int = 300) -> Optional[Dict[str, str]]:
        """
        Получить номер и дождаться SMS кода (упрощенный метод)

        Args:
            service: Название сервиса
            country: Код страны
            timeout: Таймаут ожидания SMS

        Returns:
            {"phone": "+79001234567", "code": "123456"}
        """
        # Получаем номер
        number_data = self.service.get_number(service, country)
        if not number_data:
            return None

        # Ждем SMS код
        code = self.service.get_sms_code(number_data['id'], timeout)

        if code:
            return {
                'phone': number_data['phone'],
                'code': code,
                'activation_id': number_data['id']
            }

        # Если код не получен - отменяем активацию
        self.service.cancel_activation(number_data['id'])
        return None


# Примеры использования
def example_sms_activate():
    """Пример использования SMS-Activate"""
    print("=== Пример SMS-Activate ===\n")

    # ВАЖНО: Замените на ваш реальный API ключ
    API_KEY = "your_api_key_here"

    # Создаем менеджер
    manager = SMSServiceManager(SMSServiceType.SMS_ACTIVATE, API_KEY)

    # Получаем номер для Google
    print("Получение номера для Google...")
    result = manager.get_phone_and_code(service="go", country="ru", timeout=300)

    if result:
        print(f"✓ Телефон: {result['phone']}")
        print(f"✓ SMS код: {result['code']}")
    else:
        print("✗ Не удалось получить SMS код")


def example_temp_mail():
    """Пример использования TempMail"""
    print("\n=== Пример TempMail ===\n")

    service = TempMailService()

    # Создаем временный email
    email_data = service.create_email()
    if email_data:
        print(f"✓ Email создан: {email_data['email']}")

        # Ждем сообщения (раскомментируйте для теста)
        # messages = service.get_messages(email_data['email'], timeout=60)
        # if messages:
        #     print(f"✓ Получено {len(messages)} сообщений")


if __name__ == "__main__":
    print("=== SMS Service Module ===\n")
    print("Для использования:")
    print("1. Зарегистрируйтесь на sms-activate.org или 5sim.net")
    print("2. Получите API ключ")
    print("3. Используйте SMSServiceManager для работы с сервисом\n")

    # example_sms_activate()  # Раскомментируйте и добавьте API ключ
    # example_temp_mail()
