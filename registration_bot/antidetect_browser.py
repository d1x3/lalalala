"""
Antidetect Browser Manager - управление анти-детект браузерами
Поддержка: AdsPower, Dolphin Anty, MultiLogin, GoLogin
"""

import requests
import logging
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AntidetectBrowserManager:
    """Базовый менеджер для анти-детект браузеров"""

    def __init__(self, browser_type: str, api_url: str = None, api_key: str = None):
        """
        Инициализация менеджера

        Args:
            browser_type: Тип браузера (adspower, dolphin, multilogin, goLogin)
            api_url: URL API браузера
            api_key: API ключ (если требуется)
        """
        self.browser_type = browser_type.lower()
        self.api_url = api_url
        self.api_key = api_key
        self.session = requests.Session()

        logger.info(f"AntidetectBrowserManager инициализирован: {browser_type}")

    def open_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Открыть профиль браузера

        Args:
            profile_id: ID профиля

        Returns:
            Информация о профиле (включая selenium port/webdriver path)
        """
        raise NotImplementedError("Переопределите этот метод для конкретного браузера")

    def close_profile(self, profile_id: str) -> bool:
        """
        Закрыть профиль браузера

        Args:
            profile_id: ID профиля

        Returns:
            True если успешно
        """
        raise NotImplementedError("Переопределите этот метод для конкретного браузера")

    def get_selenium_driver(self, profile_id: str) -> Optional[webdriver.Chrome]:
        """
        Получить Selenium WebDriver для профиля

        Args:
            profile_id: ID профиля

        Returns:
            WebDriver или None
        """
        raise NotImplementedError("Переопределите этот метод для конкретного браузера")


class AdsPowerManager(AntidetectBrowserManager):
    """Менеджер для AdsPower"""

    def __init__(self, api_url: str = "http://local.adspower.net:50325"):
        """
        Инициализация AdsPower

        Args:
            api_url: URL локального API AdsPower
        """
        super().__init__("adspower", api_url)

    def open_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Открыть профиль AdsPower"""
        url = f"{self.api_url}/api/v1/browser/start"
        params = {
            'user_id': profile_id,
            'open_tabs': 1
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('code') == 0:
                logger.info(f"✓ Профиль AdsPower открыт: {profile_id}")
                return data['data']
            else:
                logger.error(f"✗ Ошибка открытия профиля: {data.get('msg')}")
                return None

        except Exception as e:
            logger.error(f"✗ Ошибка AdsPower API: {e}")
            return None

    def close_profile(self, profile_id: str) -> bool:
        """Закрыть профиль AdsPower"""
        url = f"{self.api_url}/api/v1/browser/stop"
        params = {'user_id': profile_id}

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('code') == 0:
                logger.info(f"✓ Профиль AdsPower закрыт: {profile_id}")
                return True
            else:
                logger.error(f"✗ Ошибка закрытия профиля: {data.get('msg')}")
                return False

        except Exception as e:
            logger.error(f"✗ Ошибка AdsPower API: {e}")
            return False

    def get_selenium_driver(self, profile_id: str) -> Optional[webdriver.Chrome]:
        """Получить Selenium WebDriver для AdsPower профиля"""
        profile_data = self.open_profile(profile_id)

        if not profile_data:
            return None

        try:
            chrome_driver = profile_data.get('webdriver')
            debugger_address = profile_data.get('ws', {}).get('selenium')

            options = webdriver.ChromeOptions()
            options.add_experimental_option("debuggerAddress", debugger_address)

            service = Service(executable_path=chrome_driver)
            driver = webdriver.Chrome(service=service, options=options)

            logger.info(f"✓ Selenium подключен к AdsPower профилю: {profile_id}")
            return driver

        except Exception as e:
            logger.error(f"✗ Ошибка подключения Selenium: {e}")
            return None


class DolphinAntyManager(AntidetectBrowserManager):
    """Менеджер для Dolphin Anty"""

    def __init__(self, api_url: str = "http://localhost:3001", api_key: str = None):
        """
        Инициализация Dolphin Anty

        Args:
            api_url: URL локального API
            api_key: API токен
        """
        super().__init__("dolphin", api_url, api_key)
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})

    def open_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Открыть профиль Dolphin Anty"""
        url = f"{self.api_url}/v1.0/browser_profiles/{profile_id}/start"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                logger.info(f"✓ Профиль Dolphin открыт: {profile_id}")
                return data['automation']
            else:
                logger.error(f"✗ Ошибка открытия профиля Dolphin")
                return None

        except Exception as e:
            logger.error(f"✗ Ошибка Dolphin API: {e}")
            return None

    def close_profile(self, profile_id: str) -> bool:
        """Закрыть профиль Dolphin Anty"""
        url = f"{self.api_url}/v1.0/browser_profiles/{profile_id}/stop"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                logger.info(f"✓ Профиль Dolphin закрыт: {profile_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"✗ Ошибка Dolphin API: {e}")
            return False

    def get_selenium_driver(self, profile_id: str) -> Optional[webdriver.Chrome]:
        """Получить Selenium WebDriver для Dolphin профиля"""
        profile_data = self.open_profile(profile_id)

        if not profile_data:
            return None

        try:
            port = profile_data.get('port')

            options = webdriver.ChromeOptions()
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")

            driver = webdriver.Chrome(options=options)

            logger.info(f"✓ Selenium подключен к Dolphin профилю: {profile_id}")
            return driver

        except Exception as e:
            logger.error(f"✗ Ошибка подключения Selenium: {e}")
            return None


# Фабрика для создания менеджера
def create_browser_manager(browser_type: str, **kwargs) -> AntidetectBrowserManager:
    """
    Создать менеджер анти-детект браузера

    Args:
        browser_type: Тип браузера (adspower, dolphin, multilogin, gologin)
        **kwargs: Дополнительные параметры (api_url, api_key, etc.)

    Returns:
        Экземпляр менеджера браузера
    """
    browser_type = browser_type.lower()

    if browser_type == "adspower":
        return AdsPowerManager(api_url=kwargs.get('api_url', "http://local.adspower.net:50325"))

    elif browser_type == "dolphin":
        return DolphinAntyManager(
            api_url=kwargs.get('api_url', "http://localhost:3001"),
            api_key=kwargs.get('api_key')
        )

    # TODO: Добавьте поддержку других браузеров
    # elif browser_type == "multilogin":
    #     return MultiLoginManager(...)
    # elif browser_type == "gologin":
    #     return GoLoginManager(...)

    else:
        raise ValueError(f"Неподдерживаемый тип браузера: {browser_type}")


# Пример использования
def test_adspower():
    """Тест AdsPower"""
    print("=== Тест AdsPower ===\n")

    manager = AdsPowerManager()

    # Замените на ваш ID профиля
    PROFILE_ID = "your_profile_id_here"

    # Открытие профиля
    print("Открытие профиля...")
    profile_data = manager.open_profile(PROFILE_ID)

    if profile_data:
        print(f"Профиль открыт: {profile_data}")

        # Получение WebDriver
        # driver = manager.get_selenium_driver(PROFILE_ID)
        # if driver:
        #     driver.get("https://picks.betr.app")
        #     time.sleep(5)
        #     driver.quit()

        # Закрытие профиля
        input("\nНажмите Enter для закрытия профиля...")
        manager.close_profile(PROFILE_ID)


if __name__ == "__main__":
    print("AntiDetect Browser Manager\n")
    print("Поддерживаемые браузеры:")
    print("  - AdsPower")
    print("  - Dolphin Anty")
    print("  - MultiLogin (TODO)")
    print("  - GoLogin (TODO)")
    print()

    # test_adspower()  # Раскомментируйте для теста
