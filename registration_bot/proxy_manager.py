"""
Proxy Manager - управление прокси и сброс IP адресов
Поддержка популярных прокси провайдеров
"""

import requests
import logging
import time
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProxyManager:
    """Базовый менеджер для работы с прокси"""

    def __init__(self, provider: str, api_key: str = None, api_url: str = None):
        """
        Инициализация менеджера прокси

        Args:
            provider: Провайдер прокси (brightdata, smartproxy, proxy6, etc.)
            api_key: API ключ провайдера
            api_url: URL API провайдера
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.api_url = api_url
        self.session = requests.Session()

        logger.info(f"ProxyManager инициализирован: {provider}")

    def rotate_ip(self, proxy_id: Optional[str] = None) -> bool:
        """
        Сменить IP адрес прокси

        Args:
            proxy_id: ID прокси (если требуется)

        Returns:
            True если успешно
        """
        raise NotImplementedError("Переопределите этот метод для конкретного провайдера")

    def get_current_ip(self) -> Optional[str]:
        """
        Получить текущий IP адрес

        Returns:
            IP адрес или None
        """
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=10)
            response.raise_for_status()
            ip = response.json().get('ip')
            logger.info(f"Текущий IP: {ip}")
            return ip
        except:
            logger.error("Не удалось получить IP")
            return None


class BrightDataProxy(ProxyManager):
    """Менеджер для Bright Data (бывший Luminati)"""

    def __init__(self, customer_id: str, zone_name: str):
        """
        Инициализация Bright Data

        Args:
            customer_id: ID клиента
            zone_name: Название зоны
        """
        super().__init__("brightdata")
        self.customer_id = customer_id
        self.zone_name = zone_name

    def rotate_ip(self, proxy_id: Optional[str] = None) -> bool:
        """
        Смена IP в Bright Data

        Note: Bright Data ротирует IP автоматически при каждом запросе
        или можно использовать session parameter
        """
        logger.info("Bright Data ротирует IP автоматически")
        return True


class SmartProxyManager(ProxyManager):
    """Менеджер для SmartProxy"""

    def __init__(self, username: str, password: str):
        """
        Инициализация SmartProxy

        Args:
            username: Имя пользователя
            password: Пароль
        """
        super().__init__("smartproxy")
        self.username = username
        self.password = password

    def rotate_ip(self, proxy_id: Optional[str] = None) -> bool:
        """
        Смена IP в SmartProxy

        Note: SmartProxy ротирует IP автоматически
        """
        logger.info("SmartProxy ротирует IP автоматически")
        return True


class Proxy6Manager(ProxyManager):
    """Менеджер для Proxy6.net"""

    BASE_URL = "https://proxy6.net/api"

    def __init__(self, api_key: str):
        """
        Инициализация Proxy6

        Args:
            api_key: API ключ
        """
        super().__init__("proxy6", api_key, self.BASE_URL)

    def rotate_ip(self, proxy_id: Optional[str] = None) -> bool:
        """Смена IP в Proxy6"""
        # Proxy6 не имеет API для смены IP
        # Обычно используются статические прокси
        logger.warning("Proxy6 не поддерживает автоматическую смену IP")
        return False

    def get_proxy_list(self) -> Optional[Dict]:
        """Получить список прокси"""
        url = f"{self.BASE_URL}/{self.api_key}/getproxy"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'yes':
                logger.info(f"Получен список прокси: {len(data.get('list', {}))} шт.")
                return data.get('list')
            else:
                logger.error(f"Ошибка получения прокси: {data.get('error')}")
                return None

        except Exception as e:
            logger.error(f"Ошибка Proxy6 API: {e}")
            return None


class WebshareProxyManager(ProxyManager):
    """Менеджер для Webshare.io"""

    BASE_URL = "https://proxy.webshare.io/api/v2"

    def __init__(self, api_key: str):
        """
        Инициализация Webshare

        Args:
            api_key: API ключ
        """
        super().__init__("webshare", api_key, self.BASE_URL)
        self.session.headers.update({'Authorization': f'Token {api_key}'})

    def rotate_ip(self, proxy_id: Optional[str] = None) -> bool:
        """Обновить прокси в Webshare"""
        url = f"{self.BASE_URL}/proxy/refresh/"

        try:
            response = self.session.post(url, timeout=30)
            response.raise_for_status()

            logger.info("✓ IP адреса обновлены в Webshare")
            return True

        except Exception as e:
            logger.error(f"✗ Ошибка Webshare API: {e}")
            return False

    def get_proxy_list(self) -> Optional[list]:
        """Получить список прокси"""
        url = f"{self.BASE_URL}/proxy/list/"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            proxies = data.get('results', [])
            logger.info(f"Получено прокси: {len(proxies)} шт.")
            return proxies

        except Exception as e:
            logger.error(f"Ошибка Webshare API: {e}")
            return None


class CustomRotatingProxy(ProxyManager):
    """
    Менеджер для кастомных rotating прокси
    (например, через изменение session ID в URL)
    """

    def __init__(self, proxy_url: str, rotation_param: str = "session"):
        """
        Инициализация кастомного прокси

        Args:
            proxy_url: URL прокси
            rotation_param: Параметр для ротации (обычно session ID)
        """
        super().__init__("custom")
        self.proxy_url = proxy_url
        self.rotation_param = rotation_param
        self.session_counter = 0

    def rotate_ip(self, proxy_id: Optional[str] = None) -> bool:
        """
        Смена IP через изменение session ID

        Note: Это концептуальный метод - реальная ротация происходит
        при использовании прокси с новым session ID
        """
        self.session_counter += 1
        logger.info(f"✓ Session ID изменен: {self.session_counter}")
        return True

    def get_proxy_string(self) -> str:
        """
        Получить строку прокси с текущим session ID

        Returns:
            Строка прокси для использования
        """
        # Пример: http://user-session123:password@proxy.com:8080
        return f"{self.proxy_url}?{self.rotation_param}={self.session_counter}"


# Фабрика для создания менеджера
def create_proxy_manager(provider: str, **kwargs) -> ProxyManager:
    """
    Создать менеджер прокси

    Args:
        provider: Провайдер (brightdata, smartproxy, proxy6, webshare, custom)
        **kwargs: Параметры для конкретного провайдера

    Returns:
        Экземпляр менеджера прокси
    """
    provider = provider.lower()

    if provider == "brightdata":
        return BrightDataProxy(
            customer_id=kwargs['customer_id'],
            zone_name=kwargs['zone_name']
        )

    elif provider == "smartproxy":
        return SmartProxyManager(
            username=kwargs['username'],
            password=kwargs['password']
        )

    elif provider == "proxy6":
        return Proxy6Manager(api_key=kwargs['api_key'])

    elif provider == "webshare":
        return WebshareProxyManager(api_key=kwargs['api_key'])

    elif provider == "custom":
        return CustomRotatingProxy(
            proxy_url=kwargs['proxy_url'],
            rotation_param=kwargs.get('rotation_param', 'session')
        )

    else:
        raise ValueError(f"Неподдерживаемый провайдер: {provider}")


# Пример использования
def test_proxy_manager():
    """Тест менеджера прокси"""
    print("=== Proxy Manager Test ===\n")

    # Пример с Webshare
    # manager = WebshareProxyManager(api_key="YOUR_API_KEY")
    #
    # print("Текущий IP:")
    # manager.get_current_ip()
    #
    # print("\nСмена IP...")
    # manager.rotate_ip()
    # time.sleep(2)
    #
    # print("\nНовый IP:")
    # manager.get_current_ip()

    # Пример с кастомным прокси
    custom_proxy = CustomRotatingProxy(
        proxy_url="http://user:pass@proxy.example.com:8080"
    )

    for i in range(3):
        proxy_string = custom_proxy.get_proxy_string()
        print(f"Итерация {i+1}: {proxy_string}")
        custom_proxy.rotate_ip()


if __name__ == "__main__":
    print("Proxy Manager\n")
    print("Поддерживаемые провайдеры:")
    print("  - Bright Data (Luminati)")
    print("  - SmartProxy")
    print("  - Proxy6.net")
    print("  - Webshare.io")
    print("  - Custom Rotating Proxy")
    print()

    test_proxy_manager()
