"""
Screen Automation Bot
Бот для автоматизации действий на экране, имитирующий поведение человека
"""

import pyautogui
import time
import random
import logging
from typing import Tuple, List, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScreenBot:
    """Бот для автоматизации действий на экране"""

    def __init__(self, human_like: bool = True):
        """
        Инициализация бота

        Args:
            human_like: Если True, добавляет случайные задержки и движения как у человека
        """
        self.human_like = human_like
        # Защита от случайных ошибок - возможность прервать скрипт движением мыши в угол
        pyautogui.FAILSAFE = True
        # Задержка между действиями PyAutoGUI
        pyautogui.PAUSE = 0.5 if human_like else 0.1

        logger.info("ScreenBot инициализирован")
        screen_size = pyautogui.size()
        logger.info(f"Размер экрана: {screen_size.width}x{screen_size.height}")

    def human_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """Случайная задержка для имитации человека"""
        if self.human_like:
            delay = random.uniform(min_sec, max_sec)
            time.sleep(delay)
        else:
            time.sleep(0.1)

    def move_mouse(self, x: int, y: int, duration: Optional[float] = None):
        """
        Перемещение мыши к координатам

        Args:
            x, y: Координаты назначения
            duration: Длительность перемещения (автоматически если None)
        """
        if duration is None:
            duration = random.uniform(0.3, 0.8) if self.human_like else 0.1

        logger.info(f"Перемещение мыши к ({x}, {y})")
        pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeOutQuad)
        self.human_delay(0.1, 0.3)

    def click(self, x: Optional[int] = None, y: Optional[int] = None,
              clicks: int = 1, button: str = 'left'):
        """
        Клик мышью

        Args:
            x, y: Координаты клика (если None - клик в текущей позиции)
            clicks: Количество кликов
            button: 'left', 'right' или 'middle'
        """
        if x is not None and y is not None:
            self.move_mouse(x, y)

        logger.info(f"Клик {button} кнопкой ({clicks}x) на позиции {pyautogui.position()}")
        pyautogui.click(clicks=clicks, button=button)
        self.human_delay(0.2, 0.5)

    def type_text(self, text: str, interval: Optional[float] = None):
        """
        Ввод текста с клавиатуры

        Args:
            text: Текст для ввода
            interval: Интервал между нажатиями клавиш
        """
        if interval is None:
            interval = random.uniform(0.05, 0.15) if self.human_like else 0.01

        logger.info(f"Ввод текста: {text[:50]}...")
        pyautogui.typewrite(text, interval=interval)
        self.human_delay(0.2, 0.5)

    def press_key(self, key: str, presses: int = 1):
        """
        Нажатие клавиши

        Args:
            key: Название клавиши ('enter', 'esc', 'tab', и т.д.)
            presses: Количество нажатий
        """
        logger.info(f"Нажатие клавиши '{key}' ({presses}x)")
        pyautogui.press(key, presses=presses)
        self.human_delay(0.2, 0.4)

    def hotkey(self, *keys):
        """
        Комбинация клавиш (например, Ctrl+C)

        Args:
            *keys: Клавиши для нажатия одновременно
        """
        logger.info(f"Нажатие комбинации клавиш: {'+'.join(keys)}")
        pyautogui.hotkey(*keys)
        self.human_delay(0.2, 0.4)

    def scroll(self, clicks: int, direction: str = 'down'):
        """
        Прокрутка колесом мыши

        Args:
            clicks: Количество "кликов" колеса
            direction: 'up' или 'down'
        """
        scroll_amount = -clicks if direction == 'down' else clicks
        logger.info(f"Прокрутка {direction} на {clicks} кликов")
        pyautogui.scroll(scroll_amount)
        self.human_delay(0.3, 0.6)

    def screenshot(self, region: Optional[Tuple[int, int, int, int]] = None,
                   filename: Optional[str] = None):
        """
        Снимок экрана

        Args:
            region: Область для скриншота (x, y, width, height)
            filename: Имя файла для сохранения

        Returns:
            PIL Image объект
        """
        logger.info(f"Создание скриншота: {filename or 'в память'}")
        screenshot = pyautogui.screenshot(region=region)

        if filename:
            screenshot.save(filename)
            logger.info(f"Скриншот сохранен: {filename}")

        return screenshot

    def find_on_screen(self, image_path: str, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        Поиск изображения на экране

        Args:
            image_path: Путь к изображению для поиска
            confidence: Уровень совпадения (0-1)

        Returns:
            Координаты центра найденного изображения или None
        """
        try:
            logger.info(f"Поиск изображения: {image_path}")
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)

            if location:
                logger.info(f"Изображение найдено: {location}")
                return location
            else:
                logger.warning(f"Изображение не найдено: {image_path}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при поиске изображения: {e}")
            return None

    def wait_for_image(self, image_path: str, timeout: int = 10,
                       check_interval: float = 0.5) -> Optional[Tuple[int, int]]:
        """
        Ожидание появления изображения на экране

        Args:
            image_path: Путь к изображению
            timeout: Таймаут в секундах
            check_interval: Интервал проверки

        Returns:
            Координаты или None при таймауте
        """
        logger.info(f"Ожидание появления изображения: {image_path} (таймаут: {timeout}с)")
        start_time = time.time()

        while time.time() - start_time < timeout:
            location = self.find_on_screen(image_path)
            if location:
                return location
            time.sleep(check_interval)

        logger.warning(f"Таймаут ожидания изображения: {image_path}")
        return None

    def execute_sequence(self, sequence: List[dict]):
        """
        Выполнение последовательности действий

        Args:
            sequence: Список действий в формате:
                [
                    {'action': 'move', 'x': 100, 'y': 200},
                    {'action': 'click'},
                    {'action': 'type', 'text': 'Hello'},
                    {'action': 'press', 'key': 'enter'},
                    {'action': 'wait', 'seconds': 2},
                ]
        """
        logger.info(f"Выполнение последовательности из {len(sequence)} действий")

        for i, step in enumerate(sequence, 1):
            action = step.get('action')
            logger.info(f"Шаг {i}/{len(sequence)}: {action}")

            try:
                if action == 'move':
                    self.move_mouse(step['x'], step['y'])

                elif action == 'click':
                    x = step.get('x')
                    y = step.get('y')
                    clicks = step.get('clicks', 1)
                    button = step.get('button', 'left')
                    self.click(x, y, clicks, button)

                elif action == 'type':
                    self.type_text(step['text'])

                elif action == 'press':
                    self.press_key(step['key'], step.get('presses', 1))

                elif action == 'hotkey':
                    self.hotkey(*step['keys'])

                elif action == 'scroll':
                    self.scroll(step.get('clicks', 3), step.get('direction', 'down'))

                elif action == 'wait':
                    seconds = step.get('seconds', 1)
                    logger.info(f"Ожидание {seconds} секунд")
                    time.sleep(seconds)

                elif action == 'screenshot':
                    self.screenshot(filename=step.get('filename'))

                elif action == 'find_and_click':
                    location = self.find_on_screen(step['image'], step.get('confidence', 0.8))
                    if location:
                        self.click(location[0], location[1])
                    else:
                        logger.error(f"Не удалось найти изображение: {step['image']}")
                        if step.get('required', False):
                            raise Exception(f"Обязательное изображение не найдено: {step['image']}")

                else:
                    logger.warning(f"Неизвестное действие: {action}")

            except Exception as e:
                logger.error(f"Ошибка на шаге {i}: {e}")
                if step.get('critical', False):
                    raise
                continue

        logger.info("Последовательность выполнена")


def example_usage():
    """Пример использования бота"""
    # Создаем бота с имитацией человеческого поведения
    bot = ScreenBot(human_like=True)

    # Пример 1: Простая последовательность
    print("\n=== Пример 1: Простая последовательность ===")
    sequence = [
        {'action': 'wait', 'seconds': 2},
        {'action': 'move', 'x': 500, 'y': 500},
        {'action': 'click'},
        {'action': 'type', 'text': 'Привет, мир!'},
        {'action': 'press', 'key': 'enter'},
    ]
    # bot.execute_sequence(sequence)  # Раскомментируйте для выполнения

    # Пример 2: Работа с браузером
    print("\n=== Пример 2: Последовательность с поиском изображения ===")
    browser_sequence = [
        {'action': 'hotkey', 'keys': ['ctrl', 't']},  # Новая вкладка
        {'action': 'wait', 'seconds': 1},
        {'action': 'type', 'text': 'https://google.com'},
        {'action': 'press', 'key': 'enter'},
        {'action': 'wait', 'seconds': 3},
        # {'action': 'find_and_click', 'image': 'search_box.png', 'required': True},
        {'action': 'screenshot', 'filename': 'result.png'},
    ]
    # bot.execute_sequence(browser_sequence)  # Раскомментируйте для выполнения

    print("\n=== Бот готов к работе! ===")
    print("Используйте bot.execute_sequence() для выполнения действий")
    print("ВНИМАНИЕ: Переместите мышь в верхний левый угол экрана для экстренной остановки")


if __name__ == "__main__":
    example_usage()
