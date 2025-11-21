"""
Browser Automation - автоматизация браузера для регистрации аккаунтов
Использует undetected-chromedriver для обхода детекции ботов
"""

import time
import logging
import random
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

try:
    import undetected_chromedriver as uc
    UNDETECTED_AVAILABLE = True
except ImportError:
    UNDETECTED_AVAILABLE = False
    logging.warning("undetected-chromedriver не установлен. Используется обычный ChromeDriver")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrowserBot:
    """Бот для автоматизации браузера"""

    def __init__(self, headless: bool = False, use_undetected: bool = True):
        """
        Инициализация браузера

        Args:
            headless: Запуск браузера в фоновом режиме
            use_undetected: Использовать undetected-chromedriver для обхода детекции
        """
        self.driver = None
        self.headless = headless
        self.use_undetected = use_undetected and UNDETECTED_AVAILABLE
        self.wait = None

        self._init_browser()

    def _init_browser(self):
        """Инициализация браузера"""
        logger.info("Инициализация браузера...")

        try:
            if self.use_undetected:
                # Undetected ChromeDriver - обход детекции автоматизации
                options = uc.ChromeOptions()
                if self.headless:
                    options.add_argument('--headless')

                # Дополнительные опции для "человекоподобности"
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--no-sandbox')
                options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

                self.driver = uc.Chrome(options=options, version_main=120)
                logger.info("Используется undetected-chromedriver")

            else:
                # Обычный ChromeDriver
                options = webdriver.ChromeOptions()
                if self.headless:
                    options.add_argument('--headless')

                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--no-sandbox')

                self.driver = webdriver.Chrome(options=options)
                logger.info("Используется обычный ChromeDriver")

            # Установка таймаута ожидания
            self.wait = WebDriverWait(self.driver, 10)

            # Установка размера окна
            self.driver.set_window_size(1920, 1080)

            logger.info("Браузер успешно инициализирован")

        except Exception as e:
            logger.error(f"Ошибка инициализации браузера: {e}")
            raise

    def human_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """Случайная задержка для имитации человека"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def navigate_to(self, url: str):
        """
        Переход на URL

        Args:
            url: URL для перехода
        """
        logger.info(f"Переход на: {url}")
        self.driver.get(url)
        self.human_delay(1, 2)

    def find_element(self, by: By, value: str, timeout: int = 10):
        """
        Поиск элемента на странице

        Args:
            by: Тип селектора (By.ID, By.XPATH, и т.д.)
            value: Значение селектора
            timeout: Таймаут ожидания

        Returns:
            WebElement или None
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            logger.info(f"Элемент найден: {by}={value}")
            return element
        except TimeoutException:
            logger.warning(f"Элемент не найден: {by}={value}")
            return None

    def click_element(self, by: By, value: str, timeout: int = 10):
        """
        Клик по элементу

        Args:
            by: Тип селектора
            value: Значение селектора
            timeout: Таймаут ожидания

        Returns:
            True если успешно, False если элемент не найден
        """
        element = self.find_element(by, value, timeout)
        if element:
            # Прокрутка к элементу
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            self.human_delay(0.3, 0.7)

            # Клик
            element.click()
            logger.info(f"Клик по элементу: {by}={value}")
            self.human_delay(0.5, 1.0)
            return True
        return False

    def type_text(self, by: By, value: str, text: str, timeout: int = 10,
                  clear_first: bool = True, human_typing: bool = True):
        """
        Ввод текста в поле

        Args:
            by: Тип селектора
            value: Значение селектора
            text: Текст для ввода
            timeout: Таймаут ожидания
            clear_first: Очистить поле перед вводом
            human_typing: Имитация человеческого набора текста

        Returns:
            True если успешно, False если элемент не найден
        """
        element = self.find_element(by, value, timeout)
        if element:
            # Клик по элементу для фокуса
            element.click()
            self.human_delay(0.2, 0.5)

            # Очистка поля
            if clear_first:
                element.clear()
                self.human_delay(0.1, 0.3)

            # Ввод текста
            if human_typing:
                # Посимвольный ввод с задержкой
                for char in text:
                    element.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
            else:
                element.send_keys(text)

            logger.info(f"Введен текст в {by}={value}")
            self.human_delay(0.3, 0.7)
            return True
        return False

    def wait_for_element(self, by: By, value: str, timeout: int = 10) -> bool:
        """
        Ожидание появления элемента

        Args:
            by: Тип селектора
            value: Значение селектора
            timeout: Таймаут ожидания

        Returns:
            True если элемент появился, False если таймаут
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((by, value)))
            logger.info(f"Элемент появился: {by}={value}")
            return True
        except TimeoutException:
            logger.warning(f"Таймаут ожидания элемента: {by}={value}")
            return False

    def wait_for_url_contains(self, text: str, timeout: int = 10) -> bool:
        """
        Ожидание изменения URL

        Args:
            text: Текст, который должен содержаться в URL
            timeout: Таймаут ожидания

        Returns:
            True если URL изменился, False если таймаут
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.url_contains(text))
            logger.info(f"URL изменился и содержит: {text}")
            return True
        except TimeoutException:
            logger.warning(f"Таймаут ожидания изменения URL: {text}")
            return False

    def get_text(self, by: By, value: str, timeout: int = 10) -> Optional[str]:
        """
        Получить текст элемента

        Args:
            by: Тип селектора
            value: Значение селектора
            timeout: Таймаут ожидания

        Returns:
            Текст элемента или None
        """
        element = self.find_element(by, value, timeout)
        if element:
            text = element.text
            logger.info(f"Получен текст элемента: {text[:50]}...")
            return text
        return None

    def take_screenshot(self, filename: str = "screenshot.png"):
        """
        Сделать скриншот страницы

        Args:
            filename: Имя файла для сохранения
        """
        self.driver.save_screenshot(filename)
        logger.info(f"Скриншот сохранен: {filename}")

    def execute_script(self, script: str):
        """
        Выполнить JavaScript код

        Args:
            script: JavaScript код

        Returns:
            Результат выполнения скрипта
        """
        return self.driver.execute_script(script)

    def scroll_to_bottom(self):
        """Прокрутка страницы вниз"""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.human_delay(0.5, 1.0)

    def scroll_to_element(self, by: By, value: str):
        """
        Прокрутка к элементу

        Args:
            by: Тип селектора
            value: Значение селектора
        """
        element = self.find_element(by, value)
        if element:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            self.human_delay(0.3, 0.7)

    def switch_to_iframe(self, by: By, value: str, timeout: int = 10) -> bool:
        """
        Переключение на iframe

        Args:
            by: Тип селектора
            value: Значение селектора
            timeout: Таймаут ожидания

        Returns:
            True если успешно, False если iframe не найден
        """
        element = self.find_element(by, value, timeout)
        if element:
            self.driver.switch_to.frame(element)
            logger.info("Переключение на iframe")
            return True
        return False

    def switch_to_default_content(self):
        """Возврат к основному контенту из iframe"""
        self.driver.switch_to.default_content()
        logger.info("Возврат к основному контенту")

    def get_current_url(self) -> str:
        """Получить текущий URL"""
        return self.driver.current_url

    def close(self):
        """Закрытие браузера"""
        if self.driver:
            logger.info("Закрытие браузера...")
            self.driver.quit()
            self.driver = None

    def __enter__(self):
        """Поддержка context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматическое закрытие браузера"""
        self.close()


# Пример использования
def example_google_search():
    """Пример: поиск в Google"""
    with BrowserBot(headless=False, use_undetected=True) as bot:
        # Переход на Google
        bot.navigate_to("https://www.google.com")

        # Поиск поля ввода и ввод запроса
        bot.type_text(By.NAME, "q", "python automation", human_typing=True)

        # Нажатие Enter
        element = bot.find_element(By.NAME, "q")
        if element:
            element.send_keys(Keys.RETURN)

        # Ожидание результатов
        bot.wait_for_element(By.ID, "search", timeout=5)

        # Скриншот результатов
        bot.take_screenshot("google_search_results.png")

        time.sleep(2)


if __name__ == "__main__":
    print("=== Пример автоматизации браузера ===\n")
    print("Запуск примера поиска в Google...\n")
    example_google_search()
    print("\n✓ Пример выполнен!")
    print("✓ Скриншот сохранен: google_search_results.png")
