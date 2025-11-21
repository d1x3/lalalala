"""
Registration Bot - Автоматический бот для регистрации аккаунтов

Модули:
- data_manager: Управление данными аккаунтов
- browser_automation: Автоматизация браузера
- geelark_automation: Автоматизация Geelark эмулятора
- sms_service: Получение SMS кодов
- registration_bot: Главный оркестратор
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .registration_bot import RegistrationBot
from .data_manager import DataManager, AccountData
from .browser_automation import BrowserBot
from .geelark_automation import GeelarkBot
from .sms_service import SMSServiceManager, SMSServiceType, TempMailService

__all__ = [
    'RegistrationBot',
    'DataManager',
    'AccountData',
    'BrowserBot',
    'GeelarkBot',
    'SMSServiceManager',
    'SMSServiceType',
    'TempMailService',
]
