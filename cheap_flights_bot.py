#!/usr/bin/env python3
"""
Бот для поиска дешевых авиабилетов Москва → Уфа
Автор: AI Assistant
"""

import json
import logging
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Set, Dict, List

import flight_config as config
from flight_finder import FlightFinder, format_flight_message
from telegram_notifier import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cheap_flights_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CheapFlightsBot:
    """Основной класс бота для поиска дешевых билетов"""

    def __init__(self):
        self.flight_finder = FlightFinder()
        self.telegram = TelegramNotifier(config.TELEGRAM_BOT_TOKEN)
        self.found_flights_file = Path(config.FOUND_FLIGHTS_FILE)
        self.notified_flights: Set[str] = self._load_notified_flights()

    def _load_notified_flights(self) -> Set[str]:
        """Загрузка списка уже отправленных билетов"""
        if self.found_flights_file.exists():
            try:
                with open(self.found_flights_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('notified_flights', []))
            except Exception as e:
                logger.error(f"Ошибка загрузки истории: {e}")

        return set()

    def _save_notified_flights(self):
        """Сохранение списка отправленных билетов"""
        try:
            with open(self.found_flights_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'notified_flights': list(self.notified_flights),
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения истории: {e}")

    def _get_flight_key(self, flight: Dict) -> str:
        """Генерация уникального ключа для билета"""
        return f"{flight.get('origin')}_{flight.get('destination')}_{flight.get('departure_date')}_{flight.get('price')}_{flight.get('airline')}"

    def search_and_notify(self) -> int:
        """
        Поиск билетов и отправка уведомлений

        Returns:
            Количество отправленных уведомлений
        """
        logger.info("=" * 50)
        logger.info("Начало поиска дешевых билетов...")
        logger.info(f"Маршрут: {config.ORIGIN_CITY} → {config.DESTINATION_CITY}")
        logger.info(f"Максимальная цена: {config.MAX_PRICE} ₽")
        logger.info("=" * 50)

        # Поиск билетов
        flights = self.flight_finder.search_all_dates()

        if not flights:
            logger.info("Билеты не найдены")
            return 0

        # Удаляем дубликаты
        flights = self.flight_finder.deduplicate_flights(flights)

        logger.info(f"Найдено уникальных билетов: {len(flights)}")

        # Фильтруем новые билеты
        new_flights = []
        for flight in flights:
            flight_key = self._get_flight_key(flight)
            if flight_key not in self.notified_flights:
                new_flights.append(flight)

        if not new_flights:
            logger.info("Новых билетов не найдено")
            return 0

        logger.info(f"Найдено новых билетов: {len(new_flights)}")

        # Отправляем уведомления
        notifications_sent = 0
        for flight in new_flights:
            try:
                message = format_flight_message(flight)
                if self.telegram.send_flight_notification(message):
                    flight_key = self._get_flight_key(flight)
                    self.notified_flights.add(flight_key)
                    notifications_sent += 1
                    logger.info(f"Отправлено уведомление о билете: {flight.get('price')} ₽")

                    # Небольшая задержка между сообщениями
                    time.sleep(1)
                else:
                    logger.error(f"Не удалось отправить уведомление о билете")

            except Exception as e:
                logger.error(f"Ошибка отправки уведомления: {e}")

        # Сохраняем обновленный список
        self._save_notified_flights()

        logger.info(f"Отправлено уведомлений: {notifications_sent}")
        return notifications_sent

    def run_once(self) -> bool:
        """
        Однократный запуск поиска

        Returns:
            True если успешно, False в противном случае
        """
        try:
            self.search_and_notify()
            return True
        except Exception as e:
            logger.error(f"Ошибка при поиске билетов: {e}", exc_info=True)
            return False

    def run_continuous(self):
        """Непрерывный запуск с интервалом проверки"""
        logger.info("Запуск бота в режиме непрерывной работы")
        logger.info(f"Интервал проверки: {config.CHECK_INTERVAL} секунд ({config.CHECK_INTERVAL // 60} минут)")

        # Тестируем подключение к Telegram
        if not self.telegram.test_connection():
            logger.error("Не удалось подключиться к Telegram. Проверьте токен бота.")
            return

        # Отправляем стартовое сообщение
        self.telegram.send_startup_message()

        iteration = 0
        while True:
            try:
                iteration += 1
                logger.info(f"\n{'=' * 60}")
                logger.info(f"Итерация #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'=' * 60}")

                self.run_once()

                logger.info(f"Следующая проверка через {config.CHECK_INTERVAL // 60} минут")
                logger.info(f"{'=' * 60}\n")

                time.sleep(config.CHECK_INTERVAL)

            except KeyboardInterrupt:
                logger.info("\n\nОстановка бота по запросу пользователя")
                break
            except Exception as e:
                logger.error(f"Критическая ошибка: {e}", exc_info=True)
                logger.info(f"Повтор через {config.CHECK_INTERVAL} секунд...")
                time.sleep(config.CHECK_INTERVAL)


def main():
    """Главная функция"""
    print("=" * 60)
    print("🤖 БОТ ПОИСКА ДЕШЕВЫХ АВИАБИЛЕТОВ")
    print("=" * 60)
    print(f"Маршрут: {config.ORIGIN_CITY} → {config.DESTINATION_CITY}")
    print(f"Максимальная цена: {config.MAX_PRICE:,.0f} ₽")
    print("\nДаты поиска:")
    for date_config in config.DEPARTURE_DATES:
        date = date_config['date']
        time_pref = date_config.get('time_preference', 'any')
        if time_pref == 'evening':
            time_desc = "вечер"
        elif time_pref == 'morning':
            time_desc = "утро"
        else:
            time_desc = "любое время"
        print(f"  • {date} ({time_desc})")
    print("=" * 60)
    print()

    # Создаем бота
    bot = CheapFlightsBot()

    # Определяем режим работы
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Однократный запуск
        print("Режим: Однократный поиск\n")
        bot.run_once()
    else:
        # Непрерывный режим
        print("Режим: Непрерывная работа")
        print(f"Интервал проверки: {config.CHECK_INTERVAL // 60} минут")
        print("\nДля остановки нажмите Ctrl+C")
        print("=" * 60)
        print()

        # Важное примечание для пользователя
        print("⚠️  ВАЖНО: Перед запуском отправьте команду /start боту в Telegram!")
        print(f"    Токен бота: {config.TELEGRAM_BOT_TOKEN[:20]}...")
        print()
        print("Начало работы через 5 секунд...")
        time.sleep(5)

        bot.run_continuous()


if __name__ == '__main__':
    main()
