"""
Registration Bot - главный оркестратор для автоматической регистрации аккаунтов
Координирует работу браузера, эмулятора Geelark и SMS сервисов
"""

import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path
import yaml

from data_manager import DataManager, AccountData
from browser_automation import BrowserBot
from geelark_automation import GeelarkBot
from sms_service import SMSServiceManager, SMSServiceType, TempMailService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RegistrationBot:
    """Главный бот для автоматической регистрации аккаунтов"""

    def __init__(self, config_file: str = "config.yaml"):
        """
        Инициализация бота

        Args:
            config_file: Путь к файлу конфигурации
        """
        self.config = self._load_config(config_file)

        # Инициализация компонентов
        self.data_manager: Optional[DataManager] = None
        self.browser_bot: Optional[BrowserBot] = None
        self.geelark_bot: Optional[GeelarkBot] = None
        self.sms_manager: Optional[SMSServiceManager] = None
        self.temp_mail: Optional[TempMailService] = None

        self._init_components()

        logger.info("RegistrationBot инициализирован")

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Загрузка конфигурации из файла"""
        config_path = Path(config_file)

        if not config_path.exists():
            logger.warning(f"Файл конфигурации не найден: {config_file}")
            return self._get_default_config()

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        logger.info(f"Конфигурация загружена из: {config_file}")
        return config

    def _get_default_config(self) -> Dict[str, Any]:
        """Конфигурация по умолчанию"""
        return {
            'data': {
                'source': 'accounts.json',
            },
            'browser': {
                'headless': False,
                'use_undetected': True,
            },
            'geelark': {
                'window_title': 'Geelark',
                'templates_dir': 'templates',
            },
            'sms': {
                'service_type': 'sms_activate',  # или '5sim'
                'api_key': '',  # Заполните ваш API ключ
            },
            'registration': {
                'use_temp_mail': True,  # Использовать временную почту
                'sms_timeout': 300,  # Таймаут ожидания SMS в секундах
                'retry_on_failure': True,
                'max_retries': 3,
            }
        }

    def _init_components(self):
        """Инициализация компонентов бота"""
        # Data Manager
        data_source = self.config.get('data', {}).get('source', 'accounts.json')
        self.data_manager = DataManager(data_source)

        # Browser (создается по требованию для экономии ресурсов)
        # self.browser_bot будет создан в start_browser()

        # Geelark (создается по требованию)
        # self.geelark_bot будет создан в start_geelark()

        # SMS Service
        sms_config = self.config.get('sms', {})
        service_type_str = sms_config.get('service_type', 'sms_activate')
        api_key = sms_config.get('api_key', '')

        if api_key:
            service_type = SMSServiceType(service_type_str)
            self.sms_manager = SMSServiceManager(service_type, api_key)
            logger.info("SMS сервис инициализирован")
        else:
            logger.warning("API ключ SMS сервиса не указан")

        # Временная почта
        if self.config.get('registration', {}).get('use_temp_mail', False):
            self.temp_mail = TempMailService()

    def start_browser(self) -> BrowserBot:
        """Запуск браузера"""
        if not self.browser_bot:
            browser_config = self.config.get('browser', {})
            self.browser_bot = BrowserBot(
                headless=browser_config.get('headless', False),
                use_undetected=browser_config.get('use_undetected', True)
            )
        return self.browser_bot

    def start_geelark(self) -> GeelarkBot:
        """Запуск Geelark бота"""
        if not self.geelark_bot:
            geelark_config = self.config.get('geelark', {})
            self.geelark_bot = GeelarkBot(
                emulator_window_title=geelark_config.get('window_title', 'Geelark'),
                templates_dir=geelark_config.get('templates_dir', 'templates')
            )
        return self.geelark_bot

    def stop_browser(self):
        """Остановка браузера"""
        if self.browser_bot:
            self.browser_bot.close()
            self.browser_bot = None

    def register_account(self, account: AccountData) -> bool:
        """
        Регистрация одного аккаунта

        Args:
            account: Данные аккаунта для регистрации

        Returns:
            True если регистрация успешна, False если нет
        """
        logger.info(f"Начало регистрации аккаунта: {account.username}")

        try:
            # Обновляем статус
            account.status = 'in_progress'
            self.data_manager.save_data()

            # Пример процесса регистрации
            # Замените на вашу логику регистрации

            # Шаг 1: Получить временную почту (если нужно)
            if self.temp_mail and not account.email:
                email_data = self.temp_mail.create_email()
                if email_data:
                    account.email = email_data['email']
                    logger.info(f"Создан временный email: {account.email}")

            # Шаг 2: Получить номер телефона (если нужно)
            phone_data = None
            if self.sms_manager and not account.phone:
                logger.info("Получение номера телефона...")
                # Замените 'go' на код вашего сервиса
                phone_data = self.sms_manager.service.get_number('go', 'ru')
                if phone_data:
                    account.phone = phone_data['phone']
                    logger.info(f"Получен номер: {account.phone}")
                else:
                    raise Exception("Не удалось получить номер телефона")

            # Шаг 3: Регистрация в браузере
            browser = self.start_browser()
            success = self._register_in_browser(browser, account)

            if not success:
                raise Exception("Ошибка регистрации в браузере")

            # Шаг 4: Ожидание и ввод SMS кода (если требуется)
            if phone_data:
                logger.info("Ожидание SMS кода...")
                sms_code = self.sms_manager.service.get_sms_code(
                    phone_data['id'],
                    timeout=self.config.get('registration', {}).get('sms_timeout', 300)
                )

                if sms_code:
                    logger.info(f"Получен SMS код: {sms_code}")
                    # Ввести код в браузере
                    success = self._enter_sms_code(browser, sms_code)

                    if not success:
                        raise Exception("Не удалось ввести SMS код")

                    # Подтверждаем получение SMS
                    self.sms_manager.service.confirm_sms_received(phone_data['id'])
                else:
                    if phone_data:
                        self.sms_manager.service.cancel_activation(phone_data['id'])
                    raise Exception("Не удалось получить SMS код")

            # Шаг 5: Дополнительные действия в эмуляторе (если нужно)
            # geelark = self.start_geelark()
            # self._configure_in_geelark(geelark, account)

            # Успешная регистрация
            self.data_manager.update_account_status(account, 'success')
            logger.info(f"✓ Аккаунт {account.username} успешно зарегистрирован")
            return True

        except Exception as e:
            logger.error(f"✗ Ошибка регистрации {account.username}: {e}")
            self.data_manager.update_account_status(account, 'failed', str(e))
            return False

    def _register_in_browser(self, browser: BrowserBot, account: AccountData) -> bool:
        """
        Выполнение регистрации в браузере
        ЗАМЕНИТЕ НА ВАШУ ЛОГИКУ РЕГИСТРАЦИИ

        Args:
            browser: Экземпляр BrowserBot
            account: Данные аккаунта

        Returns:
            True если успешно
        """
        logger.info("Выполнение регистрации в браузере...")

        try:
            # Пример для регистрации на сайте (ЗАМЕНИТЕ НА ВАШ САЙТ)
            # browser.navigate_to("https://example.com/register")

            # # Заполнение формы
            # browser.type_text(By.NAME, "username", account.username)
            # browser.type_text(By.NAME, "email", account.email)
            # browser.type_text(By.NAME, "password", account.password)

            # if account.phone:
            #     browser.type_text(By.NAME, "phone", account.phone)

            # # Отправка формы
            # browser.click_element(By.CSS_SELECTOR, "button[type='submit']")

            # # Ожидание успешной регистрации
            # browser.wait_for_url_contains("success", timeout=10)

            logger.info("Регистрация в браузере выполнена")
            return True

        except Exception as e:
            logger.error(f"Ошибка в _register_in_browser: {e}")
            return False

    def _enter_sms_code(self, browser: BrowserBot, code: str) -> bool:
        """
        Ввод SMS кода в браузере
        ЗАМЕНИТЕ НА ВАШУ ЛОГИКУ

        Args:
            browser: Экземпляр BrowserBot
            code: SMS код

        Returns:
            True если успешно
        """
        logger.info(f"Ввод SMS кода: {code}")

        try:
            # Пример (ЗАМЕНИТЕ НА ВАШ САЙТ)
            # browser.type_text(By.NAME, "verification_code", code)
            # browser.click_element(By.CSS_SELECTOR, "button[type='submit']")
            # browser.wait_for_url_contains("verified", timeout=10)

            return True

        except Exception as e:
            logger.error(f"Ошибка ввода SMS кода: {e}")
            return False

    def _configure_in_geelark(self, geelark: GeelarkBot, account: AccountData):
        """
        Дополнительная настройка в эмуляторе Geelark
        ЗАМЕНИТЕ НА ВАШУ ЛОГИКУ

        Args:
            geelark: Экземпляр GeelarkBot
            account: Данные аккаунта
        """
        logger.info("Настройка в эмуляторе Geelark...")

        try:
            # Пример последовательности действий в эмуляторе
            # sequence = [
            #     {'action': 'click', 'x': 200, 'y': 400},
            #     {'action': 'type', 'text': account.username},
            #     {'action': 'wait', 'seconds': 2},
            # ]
            # geelark.execute_sequence(sequence)

            pass

        except Exception as e:
            logger.error(f"Ошибка в Geelark: {e}")

    def run_batch_registration(self, max_accounts: Optional[int] = None):
        """
        Массовая регистрация аккаунтов

        Args:
            max_accounts: Максимальное количество аккаунтов для обработки (None = все)
        """
        logger.info("=== Запуск массовой регистрации ===")

        # Статистика
        stats = self.data_manager.get_statistics()
        logger.info(f"Всего аккаунтов: {stats['total']}")
        logger.info(f"Ожидают обработки: {stats['pending']}")

        processed = 0

        while True:
            # Получаем следующий аккаунт
            account = self.data_manager.get_next_account()

            if not account:
                logger.info("Нет аккаунтов для обработки")
                break

            # Регистрируем аккаунт
            success = self.register_account(account)

            processed += 1

            # Пауза между регистрациями
            if self.config.get('registration', {}).get('delay_between_accounts'):
                delay = self.config['registration']['delay_between_accounts']
                logger.info(f"Пауза {delay} секунд...")
                time.sleep(delay)

            # Проверка лимита
            if max_accounts and processed >= max_accounts:
                logger.info(f"Достигнут лимит обработки: {max_accounts} аккаунтов")
                break

        # Финальная статистика
        final_stats = self.data_manager.get_statistics()
        logger.info("\n=== Результаты регистрации ===")
        logger.info(f"Обработано: {processed}")
        logger.info(f"Успешно: {final_stats['success']}")
        logger.info(f"Ошибки: {final_stats['failed']}")
        logger.info(f"Осталось: {final_stats['pending']}")

    def cleanup(self):
        """Очистка ресурсов"""
        logger.info("Очистка ресурсов...")

        if self.browser_bot:
            self.browser_bot.close()

        logger.info("Очистка завершена")


def main():
    """Главная функция"""
    print("=== Registration Bot ===\n")

    # Создаем бота
    bot = RegistrationBot(config_file="config.yaml")

    try:
        # Запуск массовой регистрации
        # Обрабатываем первые 5 аккаунтов для теста
        bot.run_batch_registration(max_accounts=5)

    except KeyboardInterrupt:
        logger.info("\nПрервано пользователем")

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)

    finally:
        bot.cleanup()


if __name__ == "__main__":
    main()
