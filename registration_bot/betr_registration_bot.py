"""
Betr Registration Bot - автоматическая регистрация на picks.betr.app
"""

import logging
import time
import random
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from daisysms_service import DaisySMSService
from betr_data_manager import BetrDataManager, BetrAccountData

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BetrRegistrationBot:
    """Бот для автоматической регистрации на Betr"""

    URL = "https://picks.betr.app/picks/home/lobby"

    def __init__(self, daisy_api_key: str, headless: bool = False):
        """
        Инициализация бота

        Args:
            daisy_api_key: API ключ DaisySMS
            headless: Запуск браузера без GUI
        """
        self.daisy_sms = DaisySMSService(daisy_api_key)
        self.headless = headless
        self.driver = None
        self.wait = None

        logger.info("BetrRegistrationBot инициализирован")

    def init_browser(self, profile_id: Optional[str] = None):
        """
        Инициализация браузера

        Args:
            profile_id: ID профиля анти-детект браузера (если используется)
        """
        # TODO: Интеграция с анти-детект браузером (AdsPower, Dolphin, etc.)
        # Сейчас используем обычный Chrome

        options = webdriver.ChromeOptions()

        if self.headless:
            options.add_argument('--headless')

        # Отключение детекции автоматизации
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # User agent
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Разрешения для геолокации
        prefs = {
            "profile.default_content_setting_values.geolocation": 1  # 1=allow, 2=block
        }
        options.add_experimental_option("prefs", prefs)

        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 20)

            # Установка геолокации (нужна координата США)
            # Пример: New York
            self.driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "accuracy": 100
            })

            logger.info("✓ Браузер инициализирован")

        except Exception as e:
            logger.error(f"✗ Ошибка инициализации браузера: {e}")
            raise

    def close_browser(self):
        """Закрытие браузера"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Браузер закрыт")
            except:
                pass
            self.driver = None

    def human_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """Случайная задержка"""
        time.sleep(random.uniform(min_sec, max_sec))

    def find_and_click(self, by: By, value: str, timeout: int = 10) -> bool:
        """
        Найти элемент и кликнуть по нему

        Args:
            by: Тип селектора
            value: Значение селектора
            timeout: Таймаут

        Returns:
            True если успешно
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            self.human_delay(0.3, 0.7)
            element.click()
            logger.info(f"✓ Клик: {value}")
            self.human_delay(0.5, 1.0)
            return True
        except TimeoutException:
            logger.warning(f"✗ Элемент не найден для клика: {value}")
            return False

    def type_text(self, by: By, value: str, text: str, clear: bool = True) -> bool:
        """
        Ввести текст в поле

        Args:
            by: Тип селектора
            value: Значение селектора
            text: Текст для ввода
            clear: Очистить поле перед вводом

        Returns:
            True если успешно
        """
        try:
            element = self.wait.until(EC.presence_of_element_located((by, value)))
            element.click()
            self.human_delay(0.2, 0.5)

            if clear:
                element.clear()
                self.human_delay(0.1, 0.3)

            # Посимвольный ввод для имитации человека
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            logger.info(f"✓ Введен текст в: {value}")
            self.human_delay(0.3, 0.7)
            return True

        except Exception as e:
            logger.error(f"✗ Ошибка ввода текста: {e}")
            return False

    def toggle_checkbox(self, by: By, value: str, check: bool = True) -> bool:
        """
        Установить/снять галочку

        Args:
            by: Тип селектора
            value: Значение селектора
            check: True - установить, False - снять

        Returns:
            True если успешно
        """
        try:
            element = self.wait.until(EC.presence_of_element_located((by, value)))
            is_checked = element.is_selected()

            if is_checked != check:
                element.click()
                logger.info(f"✓ Галочка {'установлена' if check else 'снята'}: {value}")
                self.human_delay(0.3, 0.7)

            return True

        except Exception as e:
            logger.error(f"✗ Ошибка работы с галочкой: {e}")
            return False

    def register_account(self, account: BetrAccountData) -> bool:
        """
        Регистрация одного аккаунта

        Args:
            account: Данные аккаунта

        Returns:
            True если регистрация успешна
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"РЕГИСТРАЦИЯ: {account.first_name} {account.last_name}")
        logger.info(f"{'='*60}\n")

        try:
            # Шаг 1: Открыть страницу
            logger.info("Шаг 1/12: Открытие страницы Betr...")
            self.driver.get(self.URL)
            self.human_delay(3, 5)

            # Шаг 2: Разрешить геолокацию (уже установлено в init_browser)
            logger.info("Шаг 2/12: Геолокация установлена")

            # Шаг 3: Нажать Sign Up
            logger.info("Шаг 3/12: Нажатие Sign Up...")
            # TODO: Укажите правильный селектор для кнопки Sign Up
            if not self.find_and_click(By.XPATH, "//button[contains(text(), 'Sign Up')]"):
                # Попробуйте альтернативные селекторы
                self.find_and_click(By.CSS_SELECTOR, "[data-testid='sign-up-button']")

            # Шаг 4: Ввод email и пароля
            logger.info("Шаг 4/12: Ввод email и пароля...")
            # TODO: Укажите правильные селекторы
            self.type_text(By.NAME, "email", account.email)
            self.type_text(By.NAME, "password", account.password)
            self.find_and_click(By.XPATH, "//button[contains(text(), 'Next')]")
            self.human_delay(2, 3)

            # Шаг 5: Получение номера с DaisySMS
            logger.info("Шаг 5/12: Получение номера с DaisySMS...")
            phone_data = self.daisy_sms.get_number_with_retry(service="betr", country="12", max_retries=3)

            if not phone_data:
                raise Exception("Не удалось получить номер с DaisySMS")

            account.daisy_phone = phone_data['phone']
            account.daisy_activation_id = phone_data['id']
            logger.info(f"✓ Номер получен: {account.daisy_phone}")

            # Шаг 6: Ввод номера телефона
            logger.info("Шаг 6/12: Ввод номера телефона...")
            # TODO: Укажите правильный селектор для поля телефона
            self.type_text(By.NAME, "phone", account.daisy_phone)

            # Шаг 7: Галочки
            logger.info("Шаг 7/12: Настройка галочек...")
            # TODO: Укажите правильные селекторы
            # Убрать галку enable biometrics
            self.toggle_checkbox(By.NAME, "enableBiometrics", check=False)
            # Поставить галку на соглашение
            self.toggle_checkbox(By.NAME, "termsAndConditions", check=True)

            # Нажать Next
            self.find_and_click(By.XPATH, "//button[contains(text(), 'Next')]")
            self.human_delay(2, 3)

            # Шаг 8: Получение SMS кода
            logger.info("Шаг 8/12: Ожидание SMS кода...")
            sms_code = self.daisy_sms.get_sms_code(account.daisy_activation_id, timeout=120)

            if not sms_code:
                self.daisy_sms.cancel_activation(account.daisy_activation_id)
                raise Exception("Не удалось получить SMS код")

            account.daisy_sms_code = sms_code
            logger.info(f"✓ SMS код получен: {sms_code}")

            # Шаг 9: Ввод SMS кода
            logger.info("Шаг 9/12: Ввод SMS кода...")
            # TODO: Укажите правильный селектор
            self.type_text(By.NAME, "verificationCode", sms_code)
            self.human_delay(2, 3)

            # Подтверждаем получение SMS
            self.daisy_sms.confirm_sms_received(account.daisy_activation_id)

            # Шаг 10: Дата рождения
            logger.info("Шаг 10/12: Ввод даты рождения...")
            dob = account.parse_date_of_birth()

            # TODO: Укажите правильные селекторы для даты
            # Год
            self.type_text(By.NAME, "birthYear", dob['year'])
            # Месяц
            self.type_text(By.NAME, "birthMonth", dob['month'])
            # День
            self.type_text(By.NAME, "birthDay", dob['day'])

            # Apply
            self.find_and_click(By.XPATH, "//button[contains(text(), 'Apply')]")
            self.human_delay(1, 2)
            # Next
            self.find_and_click(By.XPATH, "//button[contains(text(), 'Next')]")
            self.human_delay(2, 3)

            # Шаг 11: SSN
            logger.info("Шаг 11/12: Ввод SSN...")
            # TODO: Укажите правильный селектор
            self.type_text(By.NAME, "ssn", account.ssn_last4)
            self.find_and_click(By.XPATH, "//button[contains(text(), 'Next')]")
            self.human_delay(2, 3)

            # Шаг 12: Имя и фамилия
            logger.info("Шаг 12/12: Ввод имени и фамилии...")
            # TODO: Укажите правильные селекторы
            self.type_text(By.NAME, "firstName", account.first_name)
            self.type_text(By.NAME, "lastName", account.last_name)
            self.find_and_click(By.XPATH, "//button[contains(text(), 'Next')]")
            self.human_delay(2, 3)

            # Шаг 13: Адрес
            logger.info("Шаг 13: Ввод адреса...")
            # TODO: Укажите правильный селектор
            address_field = self.wait.until(EC.presence_of_element_located((By.NAME, "address")))
            address_field.click()
            self.human_delay(0.5, 1.0)

            # Ввод адреса посимвольно
            for char in account.address:
                address_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            # Ждем появления выпадающего списка
            self.human_delay(2, 3)

            # Выбор первого предложения из списка
            # TODO: Укажите правильный селектор для первого элемента в выпадающем списке
            try:
                first_suggestion = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".address-suggestion:first-child"))
                )
                first_suggestion.click()
                logger.info("✓ Адрес выбран из списка")
            except:
                # Если нет списка, просто продолжаем
                logger.warning("Выпадающий список адресов не найден")

            self.human_delay(1, 2)
            self.find_and_click(By.XPATH, "//button[contains(text(), 'Next')]")
            self.human_delay(2, 3)

            # Шаг 14: Проставить 4 галки
            logger.info("Шаг 14: Проставление галочек согласия...")
            # TODO: Укажите правильные селекторы для 4 галочек
            for i in range(1, 5):
                self.toggle_checkbox(By.NAME, f"consent{i}", check=True)

            # Verify Identity
            logger.info("Шаг 15: Verify Identity...")
            self.find_and_click(By.XPATH, "//button[contains(text(), 'Verify Identity')]")
            self.human_delay(5, 7)

            # Проверка результата
            # TODO: Определите как проверить успешную регистрацию
            # Например, проверка URL или наличия определенного элемента

            current_url = self.driver.current_url
            logger.info(f"Текущий URL: {current_url}")

            # Временно считаем успехом если дошли до этого момента
            logger.info(f"\n{'='*60}")
            logger.info("✓ РЕГИСТРАЦИЯ ЗАВЕРШЕНА")
            logger.info(f"{'='*60}\n")

            return True

        except Exception as e:
            logger.error(f"\n{'='*60}")
            logger.error(f"✗ ОШИБКА РЕГИСТРАЦИИ: {e}")
            logger.error(f"{'='*60}\n")

            # Отменяем активацию если есть
            if account.daisy_activation_id:
                self.daisy_sms.cancel_activation(account.daisy_activation_id)

            return False

    def screenshot(self, filename: str = "screenshot.png"):
        """Сделать скриншот"""
        if self.driver:
            self.driver.save_screenshot(filename)
            logger.info(f"Скриншот сохранен: {filename}")


# Главная функция
def main():
    """Тестовый запуск бота"""
    print("="*60)
    print("       BETR REGISTRATION BOT")
    print("="*60)
    print()

    # API ключ DaisySMS
    DAISY_API_KEY = "sXkKiQYqup71VRiMCAR1D4gG1XaDZ4"

    # Менеджер данных
    data_manager = BetrDataManager('betr_accounts.json')

    # Статистика
    stats = data_manager.get_statistics()
    print(f"Всего аккаунтов: {stats['total']}")
    print(f"Ожидают обработки: {stats['pending']}")
    print(f"Успешно: {stats['success']}")
    print(f"Ошибки: {stats['failed']}")
    print()

    # Создаем бота
    bot = BetrRegistrationBot(DAISY_API_KEY, headless=False)

    try:
        # Получаем следующий аккаунт
        account = data_manager.get_next_account()

        if not account:
            print("Нет аккаунтов для обработки")
            return

        # Инициализируем браузер
        bot.init_browser()

        # Регистрируем аккаунт
        success = bot.register_account(account)

        # Обновляем статус
        if success:
            data_manager.update_account_status(account, 'success')
        else:
            data_manager.update_account_status(account, 'failed', 'Registration error')

        # Пауза перед закрытием
        print("\nНажмите Enter для закрытия...")
        input()

    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)

    finally:
        bot.close_browser()
        print("\nРабота завершена")


if __name__ == "__main__":
    main()
