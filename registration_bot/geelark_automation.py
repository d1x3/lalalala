"""
Geelark Emulator Automation - автоматизация работы с эмулятором Geelark
Использует PyAutoGUI для управления окном эмулятора и действиями на Android
"""

import pyautogui
import time
import logging
import random
from typing import Optional, Tuple, List
from pathlib import Path
import cv2
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeelarkBot:
    """Бот для автоматизации Geelark Android эмулятора"""

    def __init__(self, emulator_window_title: str = "Geelark",
                 human_like: bool = True,
                 templates_dir: str = "templates"):
        """
        Инициализация бота для Geelark

        Args:
            emulator_window_title: Название окна эмулятора
            human_like: Имитация человеческого поведения
            templates_dir: Директория с шаблонами изображений для распознавания
        """
        self.emulator_window_title = emulator_window_title
        self.human_like = human_like
        self.templates_dir = Path(templates_dir)

        # Настройки PyAutoGUI
        pyautogui.FAILSAFE = True  # Перемещение мыши в угол для остановки
        pyautogui.PAUSE = 0.5 if human_like else 0.1

        # Границы окна эмулятора (будут определены при первом использовании)
        self.emulator_region: Optional[Tuple[int, int, int, int]] = None

        logger.info("GeelarkBot инициализирован")

        # Создание директории для шаблонов если не существует
        self.templates_dir.mkdir(exist_ok=True)

    def human_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """Случайная задержка для имитации человека"""
        if self.human_like:
            delay = random.uniform(min_sec, max_sec)
            time.sleep(delay)
        else:
            time.sleep(0.1)

    def locate_emulator_window(self) -> bool:
        """
        Поиск окна эмулятора Geelark

        Returns:
            True если окно найдено, False если нет

        Note:
            PyAutoGUI не имеет встроенных функций для поиска окон по названию.
            Нужно использовать сторонние библиотеки (pygetwindow для Windows)
            или задать регион вручную
        """
        try:
            # Попытка использовать pygetwindow (работает только на Windows)
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(self.emulator_window_title)

            if windows:
                window = windows[0]
                # Активация окна
                window.activate()
                time.sleep(0.5)

                # Получение координат окна
                self.emulator_region = (window.left, window.top, window.width, window.height)
                logger.info(f"Окно эмулятора найдено: {self.emulator_region}")
                return True
            else:
                logger.warning(f"Окно '{self.emulator_window_title}' не найдено")
                return False

        except ImportError:
            logger.warning("pygetwindow не установлен. Используйте set_emulator_region() вручную")
            return False
        except Exception as e:
            logger.error(f"Ошибка при поиске окна: {e}")
            return False

    def set_emulator_region(self, x: int, y: int, width: int, height: int):
        """
        Установка региона окна эмулятора вручную

        Args:
            x, y: Координаты левого верхнего угла
            width, height: Ширина и высота окна
        """
        self.emulator_region = (x, y, width, height)
        logger.info(f"Регион эмулятора установлен: {self.emulator_region}")

    def click(self, x: int, y: int, relative: bool = True, clicks: int = 1):
        """
        Клик по координатам

        Args:
            x, y: Координаты клика
            relative: Если True - координаты относительно окна эмулятора
            clicks: Количество кликов
        """
        if relative and self.emulator_region:
            # Координаты относительно окна эмулятора
            abs_x = self.emulator_region[0] + x
            abs_y = self.emulator_region[1] + y
        else:
            abs_x, abs_y = x, y

        logger.info(f"Клик по координатам ({abs_x}, {abs_y})")

        # Перемещение мыши
        duration = random.uniform(0.3, 0.8) if self.human_like else 0.1
        pyautogui.moveTo(abs_x, abs_y, duration=duration)
        self.human_delay(0.1, 0.3)

        # Клик
        pyautogui.click(clicks=clicks)
        self.human_delay(0.3, 0.7)

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int,
              duration: float = 0.5, relative: bool = True):
        """
        Свайп (перетаскивание пальца)

        Args:
            start_x, start_y: Начальные координаты
            end_x, end_y: Конечные координаты
            duration: Длительность свайпа
            relative: Координаты относительно окна эмулятора
        """
        if relative and self.emulator_region:
            start_x += self.emulator_region[0]
            start_y += self.emulator_region[1]
            end_x += self.emulator_region[0]
            end_y += self.emulator_region[1]

        logger.info(f"Свайп от ({start_x}, {start_y}) до ({end_x}, {end_y})")

        # Перемещение к начальной точке
        pyautogui.moveTo(start_x, start_y)
        self.human_delay(0.1, 0.2)

        # Свайп (зажать и перетащить)
        pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration, button='left')
        self.human_delay(0.3, 0.7)

    def type_text(self, text: str, interval: Optional[float] = None):
        """
        Ввод текста

        Args:
            text: Текст для ввода
            interval: Интервал между символами
        """
        if interval is None:
            interval = random.uniform(0.05, 0.15) if self.human_like else 0.01

        logger.info(f"Ввод текста: {text[:50]}...")

        for char in text:
            pyautogui.press(char)
            time.sleep(interval)

        self.human_delay(0.2, 0.5)

    def press_android_key(self, key: str):
        """
        Нажатие клавиш Android (Back, Home и т.д.)

        Args:
            key: Название клавиши

        Note:
            Координаты кнопок нужно настроить под ваш эмулятор
        """
        # Примерные координаты кнопок Android (настройте под свой эмулятор)
        android_keys = {
            'back': (50, 50),      # Кнопка Назад
            'home': (100, 50),     # Кнопка Home
            'recent': (150, 50),   # Кнопка последних приложений
        }

        if key.lower() in android_keys:
            x, y = android_keys[key.lower()]
            self.click(x, y, relative=True)
            logger.info(f"Нажата Android клавиша: {key}")
        else:
            logger.warning(f"Неизвестная Android клавиша: {key}")

    def find_image(self, template_name: str, confidence: float = 0.8,
                   region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Tuple[int, int]]:
        """
        Поиск изображения на экране

        Args:
            template_name: Имя файла шаблона в директории templates
            confidence: Уровень совпадения (0-1)
            region: Область поиска (если None - используется регион эмулятора)

        Returns:
            Координаты центра найденного изображения или None
        """
        template_path = self.templates_dir / template_name

        if not template_path.exists():
            logger.error(f"Файл шаблона не найден: {template_path}")
            return None

        search_region = region or self.emulator_region

        try:
            logger.info(f"Поиск изображения: {template_name}")
            location = pyautogui.locateCenterOnScreen(
                str(template_path),
                confidence=confidence,
                region=search_region
            )

            if location:
                logger.info(f"Изображение найдено: {location}")
                return location
            else:
                logger.warning(f"Изображение не найдено: {template_name}")
                return None

        except Exception as e:
            logger.error(f"Ошибка при поиске изображения: {e}")
            return None

    def wait_for_image(self, template_name: str, timeout: int = 10,
                      confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        Ожидание появления изображения

        Args:
            template_name: Имя файла шаблона
            timeout: Таймаут в секундах
            confidence: Уровень совпадения

        Returns:
            Координаты или None при таймауте
        """
        logger.info(f"Ожидание появления изображения: {template_name} (таймаут: {timeout}с)")
        start_time = time.time()

        while time.time() - start_time < timeout:
            location = self.find_image(template_name, confidence)
            if location:
                return location
            time.sleep(0.5)

        logger.warning(f"Таймаут ожидания изображения: {template_name}")
        return None

    def click_image(self, template_name: str, confidence: float = 0.8,
                   timeout: int = 10) -> bool:
        """
        Найти изображение и кликнуть по нему

        Args:
            template_name: Имя файла шаблона
            confidence: Уровень совпадения
            timeout: Таймаут ожидания

        Returns:
            True если успешно, False если не найдено
        """
        location = self.wait_for_image(template_name, timeout, confidence)

        if location:
            pyautogui.click(location[0], location[1])
            logger.info(f"Клик по изображению: {template_name}")
            self.human_delay(0.3, 0.7)
            return True

        return False

    def screenshot(self, filename: str = "screenshot.png",
                  region: Optional[Tuple[int, int, int, int]] = None):
        """
        Снимок экрана

        Args:
            filename: Имя файла для сохранения
            region: Область для скриншота (если None - используется регион эмулятора)
        """
        capture_region = region or self.emulator_region

        logger.info(f"Создание скриншота: {filename}")
        screenshot = pyautogui.screenshot(region=capture_region)
        screenshot.save(filename)
        logger.info(f"Скриншот сохранен: {filename}")

    def save_template(self, x: int, y: int, width: int, height: int,
                     template_name: str, relative: bool = True):
        """
        Сохранить область экрана как шаблон для распознавания

        Args:
            x, y: Координаты левого верхнего угла
            width, height: Размеры области
            template_name: Имя файла для сохранения
            relative: Координаты относительно окна эмулятора
        """
        if relative and self.emulator_region:
            x += self.emulator_region[0]
            y += self.emulator_region[1]

        region = (x, y, width, height)
        template_path = self.templates_dir / template_name

        screenshot = pyautogui.screenshot(region=region)
        screenshot.save(template_path)

        logger.info(f"Шаблон сохранен: {template_path}")

    def execute_sequence(self, sequence: List[dict]):
        """
        Выполнение последовательности действий

        Args:
            sequence: Список действий в формате:
                [
                    {'action': 'click', 'x': 100, 'y': 200},
                    {'action': 'type', 'text': 'Hello'},
                    {'action': 'swipe', 'start_x': 100, 'start_y': 500, 'end_x': 100, 'end_y': 200},
                    {'action': 'wait', 'seconds': 2},
                    {'action': 'find_and_click', 'template': 'button.png'},
                ]
        """
        logger.info(f"Выполнение последовательности из {len(sequence)} действий")

        for i, step in enumerate(sequence, 1):
            action = step.get('action')
            logger.info(f"Шаг {i}/{len(sequence)}: {action}")

            try:
                if action == 'click':
                    self.click(
                        step['x'], step['y'],
                        relative=step.get('relative', True),
                        clicks=step.get('clicks', 1)
                    )

                elif action == 'type':
                    self.type_text(step['text'], step.get('interval'))

                elif action == 'swipe':
                    self.swipe(
                        step['start_x'], step['start_y'],
                        step['end_x'], step['end_y'],
                        duration=step.get('duration', 0.5),
                        relative=step.get('relative', True)
                    )

                elif action == 'wait':
                    seconds = step.get('seconds', 1)
                    logger.info(f"Ожидание {seconds} секунд")
                    time.sleep(seconds)

                elif action == 'screenshot':
                    self.screenshot(filename=step.get('filename', 'screenshot.png'))

                elif action == 'find_and_click':
                    success = self.click_image(
                        step['template'],
                        confidence=step.get('confidence', 0.8),
                        timeout=step.get('timeout', 10)
                    )
                    if not success and step.get('required', False):
                        raise Exception(f"Обязательное изображение не найдено: {step['template']}")

                elif action == 'android_key':
                    self.press_android_key(step['key'])

                else:
                    logger.warning(f"Неизвестное действие: {action}")

            except Exception as e:
                logger.error(f"Ошибка на шаге {i}: {e}")
                if step.get('critical', False):
                    raise
                continue

        logger.info("Последовательность выполнена")


def example_usage():
    """Пример использования GeelarkBot"""
    print("=== Пример использования GeelarkBot ===\n")

    # Создаем бота
    bot = GeelarkBot(emulator_window_title="Geelark", human_like=True)

    # Поиск окна эмулятора (работает только на Windows с pygetwindow)
    # Если не работает - используйте set_emulator_region() вручную
    found = bot.locate_emulator_window()

    if not found:
        print("Окно эмулятора не найдено. Установите регион вручную:")
        print("bot.set_emulator_region(x=100, y=100, width=400, height=800)")
        # bot.set_emulator_region(x=100, y=100, width=400, height=800)

    # Пример последовательности действий
    sequence = [
        {'action': 'wait', 'seconds': 2},
        {'action': 'click', 'x': 200, 'y': 400},  # Клик в центре экрана
        {'action': 'wait', 'seconds': 1},
        {'action': 'type', 'text': 'test@example.com'},
        {'action': 'wait', 'seconds': 1},
        {'action': 'swipe', 'start_x': 200, 'start_y': 600, 'end_x': 200, 'end_y': 200},  # Свайп вверх
        {'action': 'screenshot', 'filename': 'geelark_screenshot.png'},
    ]

    # bot.execute_sequence(sequence)  # Раскомментируйте для выполнения

    print("\n✓ Бот готов к работе!")
    print("ВНИМАНИЕ: Переместите мышь в верхний левый угол для экстренной остановки")


if __name__ == "__main__":
    example_usage()
