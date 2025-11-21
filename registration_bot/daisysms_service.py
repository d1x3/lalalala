"""
DaisySMS Service - интеграция с DaisySMS API
API документация: https://daisysms.com/docs/api
"""

import requests
import time
import logging
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DaisySMSService:
    """Сервис для работы с DaisySMS API"""

    BASE_URL = "https://daisysms.com/stubs/handler_api.php"

    def __init__(self, api_key: str):
        """
        Инициализация сервиса

        Args:
            api_key: API ключ от DaisySMS
        """
        self.api_key = api_key
        self.session = requests.Session()
        logger.info("DaisySMS сервис инициализирован")

    def _make_request(self, params: Dict[str, Any]) -> str:
        """
        Выполнить запрос к API

        Args:
            params: Параметры запроса

        Returns:
            Ответ от API в виде строки
        """
        params['api_key'] = self.api_key

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            result = response.text.strip()
            logger.debug(f"API ответ: {result}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к DaisySMS: {e}")
            return ""

    def get_balance(self) -> Optional[float]:
        """
        Получить баланс аккаунта

        Returns:
            Баланс в долларах или None при ошибке
        """
        params = {'action': 'getBalance'}
        response = self._make_request(params)

        if response.startswith('ACCESS_BALANCE'):
            # Формат: ACCESS_BALANCE:50.30
            balance = float(response.split(':')[1])
            logger.info(f"Баланс: ${balance}")
            return balance

        logger.error(f"Не удалось получить баланс: {response}")
        return None

    def get_number(self, service: str, country: str = "12") -> Optional[Dict[str, Any]]:
        """
        Получить номер телефона для сервиса

        Args:
            service: Код сервиса (например, "betr" для Betr)
            country: Код страны (12 = USA)

        Returns:
            {"id": "activation_id", "phone": "+1234567890"} или None
        """
        params = {
            'action': 'getNumber',
            'service': service,
            'country': country
        }

        response = self._make_request(params)

        if response.startswith('ACCESS_NUMBER'):
            # Формат: ACCESS_NUMBER:activation_id:phone_number
            parts = response.split(':')
            if len(parts) == 3:
                activation_id = parts[1]
                phone = parts[2]

                logger.info(f"✓ Получен номер: {phone} (ID: {activation_id})")
                return {
                    'id': activation_id,
                    'phone': phone
                }

        # Обработка ошибок
        error_messages = {
            'NO_NUMBERS': 'Нет доступных номеров',
            'NO_BALANCE': 'Недостаточно средств на балансе',
            'BAD_ACTION': 'Неверное действие',
            'BAD_SERVICE': 'Неверный код сервиса',
            'BAD_KEY': 'Неверный API ключ'
        }

        error_msg = error_messages.get(response, f"Неизвестная ошибка: {response}")
        logger.error(f"✗ Не удалось получить номер: {error_msg}")
        return None

    def get_sms_code(self, activation_id: str, timeout: int = 300, check_interval: int = 5) -> Optional[str]:
        """
        Получить SMS код для активации

        Args:
            activation_id: ID активации
            timeout: Максимальное время ожидания в секундах
            check_interval: Интервал проверки в секундах

        Returns:
            SMS код или None
        """
        logger.info(f"Ожидание SMS кода для активации {activation_id}...")

        start_time = time.time()

        while time.time() - start_time < timeout:
            params = {
                'action': 'getStatus',
                'id': activation_id
            }

            response = self._make_request(params)

            if response.startswith('STATUS_OK'):
                # Формат: STATUS_OK:code
                code = response.split(':')[1]
                logger.info(f"✓ Получен SMS код: {code}")
                return code

            elif response == 'STATUS_WAIT_CODE':
                # Ожидаем SMS
                logger.debug(f"Ожидание SMS... ({int(time.time() - start_time)}с)")
                time.sleep(check_interval)

            elif response == 'STATUS_CANCEL':
                logger.warning("Активация отменена")
                return None

            elif response == 'STATUS_WAIT_RESEND':
                logger.info("Ожидание повторной отправки...")
                time.sleep(check_interval)

            else:
                logger.warning(f"Неожиданный статус: {response}")
                time.sleep(check_interval)

        logger.error(f"✗ Таймаут ожидания SMS ({timeout}с) для активации {activation_id}")
        return None

    def set_status(self, activation_id: str, status: int) -> bool:
        """
        Установить статус активации

        Args:
            activation_id: ID активации
            status: Код статуса
                1 - готов к повторной отправке
                3 - запросить еще один код
                6 - завершить успешно
                8 - отменить активацию

        Returns:
            True если успешно
        """
        params = {
            'action': 'setStatus',
            'id': activation_id,
            'status': str(status)
        }

        response = self._make_request(params)

        success_responses = {
            '1': 'ACCESS_RETRY_GET',
            '3': 'ACCESS_RETRY_GET',
            '6': 'ACCESS_ACTIVATION',
            '8': 'ACCESS_CANCEL'
        }

        expected = success_responses.get(str(status))
        if response == expected:
            logger.info(f"✓ Статус активации {activation_id} изменен на {status}")
            return True

        logger.error(f"✗ Не удалось изменить статус: {response}")
        return False

    def cancel_activation(self, activation_id: str) -> bool:
        """
        Отменить активацию

        Args:
            activation_id: ID активации

        Returns:
            True если успешно
        """
        logger.info(f"Отмена активации {activation_id}...")
        return self.set_status(activation_id, 8)

    def confirm_sms_received(self, activation_id: str) -> bool:
        """
        Подтвердить получение SMS и завершить активацию

        Args:
            activation_id: ID активации

        Returns:
            True если успешно
        """
        logger.info(f"Подтверждение получения SMS для {activation_id}...")
        return self.set_status(activation_id, 6)

    def get_prices(self, service: str = None, country: str = "12") -> Optional[Dict]:
        """
        Получить цены на номера

        Args:
            service: Код сервиса (опционально)
            country: Код страны

        Returns:
            Словарь с ценами или None
        """
        params = {
            'action': 'getPrices',
            'country': country
        }

        if service:
            params['service'] = service

        response = self._make_request(params)

        # Ответ в формате JSON
        try:
            import json
            prices = json.loads(response)
            logger.info(f"Получены цены для страны {country}")
            return prices
        except:
            logger.error(f"Не удалось получить цены: {response}")
            return None

    def get_number_with_retry(self, service: str, country: str = "12",
                             max_retries: int = 3, retry_delay: int = 5) -> Optional[Dict[str, Any]]:
        """
        Получить номер с повторными попытками

        Args:
            service: Код сервиса
            country: Код страны
            max_retries: Максимальное количество попыток
            retry_delay: Задержка между попытками в секундах

        Returns:
            Данные номера или None
        """
        for attempt in range(1, max_retries + 1):
            logger.info(f"Попытка {attempt}/{max_retries} получить номер...")

            result = self.get_number(service, country)

            if result:
                return result

            if attempt < max_retries:
                logger.info(f"Повтор через {retry_delay} секунд...")
                time.sleep(retry_delay)

        logger.error(f"Не удалось получить номер после {max_retries} попыток")
        return None


# Пример использования
def test_daisysms():
    """Тестирование DaisySMS сервиса"""
    print("=== Тест DaisySMS API ===\n")

    # ВАЖНО: Используйте ваш настоящий API ключ
    API_KEY = "sXkKiQYqup71VRiMCAR1D4gG1XaDZ4"

    service = DaisySMSService(API_KEY)

    # Проверка баланса
    print("1. Проверка баланса...")
    balance = service.get_balance()
    if balance:
        print(f"   Баланс: ${balance}\n")

    # Получение цен (опционально)
    # print("2. Получение цен...")
    # prices = service.get_prices(service="betr", country="12")
    # if prices:
    #     print(f"   Цены получены\n")

    # Получение номера (раскомментируйте для реального теста)
    # print("3. Получение номера для Betr...")
    # number_data = service.get_number(service="betr", country="12")
    #
    # if number_data:
    #     print(f"   Номер: {number_data['phone']}")
    #     print(f"   ID активации: {number_data['id']}\n")
    #
    #     # Ожидание SMS
    #     print("4. Ожидание SMS кода...")
    #     code = service.get_sms_code(number_data['id'], timeout=120)
    #
    #     if code:
    #         print(f"   SMS код: {code}\n")
    #
    #         # Подтверждение получения
    #         service.confirm_sms_received(number_data['id'])
    #     else:
    #         # Отмена если код не получен
    #         service.cancel_activation(number_data['id'])

    print("✓ Тест завершен")


if __name__ == "__main__":
    test_daisysms()
