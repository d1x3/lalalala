"""
Модуль для отправки уведомлений в Telegram
"""

import requests
import logging
from typing import Optional
import flight_config as config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram"""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_base = f"https://api.telegram.org/bot{bot_token}"
        self.chat_id = None

    def get_updates(self) -> dict:
        """Получение обновлений от бота"""
        try:
            url = f"{self.api_base}/getUpdates"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка получения обновлений: {e}")
            return {}

    def get_chat_id(self) -> Optional[str]:
        """Получение chat_id из последних сообщений"""
        try:
            updates = self.get_updates()

            if updates.get('ok') and updates.get('result'):
                # Берем последнее сообщение
                for update in reversed(updates['result']):
                    if 'message' in update:
                        chat_id = update['message']['chat']['id']
                        logger.info(f"Найден chat_id: {chat_id}")
                        return str(chat_id)

            logger.warning("Не найдено сообщений. Отправьте /start боту.")
            return None
        except Exception as e:
            logger.error(f"Ошибка получения chat_id: {e}")
            return None

    def send_message(self, message: str, chat_id: Optional[str] = None) -> bool:
        """
        Отправка сообщения в Telegram

        Args:
            message: Текст сообщения
            chat_id: ID чата (если None, попытается получить автоматически)

        Returns:
            True если успешно, False в противном случае
        """
        # Определяем chat_id
        target_chat_id = chat_id or self.chat_id

        if not target_chat_id:
            # Пытаемся получить chat_id автоматически
            target_chat_id = self.get_chat_id()
            if target_chat_id:
                self.chat_id = target_chat_id
            else:
                logger.error("Не удалось определить chat_id. Отправьте /start боту.")
                return False

        try:
            url = f"{self.api_base}/sendMessage"
            params = {
                'chat_id': target_chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': False
            }

            response = requests.post(url, json=params, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get('ok'):
                logger.info(f"Сообщение успешно отправлено в chat_id: {target_chat_id}")
                return True
            else:
                logger.error(f"Ошибка отправки сообщения: {result}")
                return False

        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в Telegram: {e}")
            return False

    def send_flight_notification(self, flight_message: str, chat_id: Optional[str] = None) -> bool:
        """Отправка уведомления о найденном билете"""
        return self.send_message(flight_message, chat_id)

    def send_startup_message(self, chat_id: Optional[str] = None) -> bool:
        """Отправка стартового сообщения"""
        message = (
            "🤖 Бот поиска дешевых билетов запущен!\n\n"
            f"📍 Маршрут: {config.ORIGIN_CITY} → {config.DESTINATION_CITY}\n"
            f"💰 Максимальная цена: {config.MAX_PRICE:,.0f} ₽\n\n"
            "Даты поиска:\n"
        )

        for date_config in config.DEPARTURE_DATES:
            date = date_config['date']
            time_pref = date_config.get('time_preference', 'any')

            if time_pref == 'evening':
                time_desc = "вечер"
            elif time_pref == 'morning':
                time_desc = "утро"
            elif time_pref == 'afternoon':
                time_desc = "день"
            else:
                time_desc = "любое время"

            message += f"  • {date} ({time_desc})\n"

        message += f"\n⏰ Проверка каждые {config.CHECK_INTERVAL // 60} минут"

        return self.send_message(message, chat_id)

    def test_connection(self) -> bool:
        """Тестирование подключения к Telegram API"""
        try:
            url = f"{self.api_base}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get('ok'):
                bot_info = result.get('result', {})
                logger.info(f"Подключение к Telegram успешно! Бот: @{bot_info.get('username')}")
                return True
            else:
                logger.error(f"Ошибка подключения: {result}")
                return False

        except Exception as e:
            logger.error(f"Ошибка тестирования подключения: {e}")
            return False
