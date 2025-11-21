#!/usr/bin/env python3
"""
Скрипт запуска Registration Bot
"""

import sys
import argparse
import logging
from pathlib import Path

# Добавляем путь к модулю
sys.path.insert(0, str(Path(__file__).parent / "registration_bot"))

from registration_bot import RegistrationBot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Registration Bot - автоматическая регистрация аккаунтов'
    )

    parser.add_argument(
        '-c', '--config',
        default='registration_bot/config.yaml',
        help='Путь к файлу конфигурации (по умолчанию: registration_bot/config.yaml)'
    )

    parser.add_argument(
        '-n', '--max-accounts',
        type=int,
        default=None,
        help='Максимальное количество аккаунтов для обработки'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Запустить браузер в headless режиме'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Тестовый запуск без реальной регистрации'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("           REGISTRATION BOT")
    print("=" * 60)
    print(f"\nКонфигурация: {args.config}")
    print(f"Максимум аккаунтов: {args.max_accounts or 'все'}")
    print(f"Headless режим: {'да' if args.headless else 'нет'}")
    print(f"Тестовый запуск: {'да' if args.dry_run else 'нет'}")
    print("\n" + "=" * 60 + "\n")

    if args.dry_run:
        logger.info("ТЕСТОВЫЙ ЗАПУСК - регистрация не будет выполнена")

    try:
        # Создаем бота
        bot = RegistrationBot(config_file=args.config)

        # Переопределяем headless если указан в аргументах
        if args.headless:
            bot.config['browser']['headless'] = True

        # Запускаем регистрацию
        if not args.dry_run:
            bot.run_batch_registration(max_accounts=args.max_accounts)
        else:
            # В тестовом режиме просто показываем статистику
            stats = bot.data_manager.get_statistics()
            print("\nСтатистика аккаунтов:")
            print(f"  Всего: {stats['total']}")
            print(f"  Ожидают: {stats['pending']}")
            print(f"  В процессе: {stats['in_progress']}")
            print(f"  Успешно: {stats['success']}")
            print(f"  Ошибки: {stats['failed']}")

    except KeyboardInterrupt:
        logger.info("\n\nПрервано пользователем (Ctrl+C)")
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"\nОшибка: файл не найден - {e}")
        logger.error("Убедитесь, что config.yaml и accounts.json существуют")
        sys.exit(1)

    except Exception as e:
        logger.error(f"\nКритическая ошибка: {e}", exc_info=True)
        sys.exit(1)

    finally:
        if 'bot' in locals():
            bot.cleanup()

    print("\n" + "=" * 60)
    print("           ЗАВЕРШЕНО")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
