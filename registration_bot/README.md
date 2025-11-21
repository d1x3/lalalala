# Registration Bot

Автоматический бот для регистрации аккаунтов с поддержкой:
- Автоматизации браузера (Selenium + undetected-chromedriver)
- Работы с эмулятором Android Geelark
- Получения SMS кодов через API сервисы
- Временной электронной почты

## Структура проекта

```
registration_bot/
├── data_manager.py          # Управление данными аккаунтов
├── browser_automation.py    # Автоматизация браузера
├── geelark_automation.py    # Автоматизация Geelark эмулятора
├── sms_service.py           # Работа с SMS сервисами
├── registration_bot.py      # Главный оркестратор
├── config.yaml              # Конфигурация
├── accounts.json            # Данные аккаунтов
├── templates/               # Шаблоны изображений для Geelark
└── README.md               # Документация
```

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Для Playwright (опционально):
```bash
playwright install chromium
```

3. Создайте конфигурационный файл `config.yaml` и заполните необходимые данные

## Настройка

### 1. SMS Сервис

Зарегистрируйтесь на одном из сервисов:
- [SMS-Activate](https://sms-activate.org/) - популярный сервис для получения SMS
- [5sim](https://5sim.net/) - альтернативный сервис

Получите API ключ и укажите его в `config.yaml`:
```yaml
sms:
  service_type: "sms_activate"
  api_key: "YOUR_API_KEY_HERE"
```

### 2. Данные аккаунтов

Подготовьте файл с данными аккаунтов в формате JSON, CSV или YAML.

Пример `accounts.json`:
```json
{
  "accounts": [
    {
      "username": "user1",
      "password": "SecurePass123!",
      "email": "",
      "phone": null,
      "first_name": "John",
      "last_name": "Doe",
      "status": "pending"
    }
  ]
}
```

### 3. Geelark Эмулятор (если используется)

1. Запустите эмулятор Geelark
2. Определите координаты окна эмулятора
3. Создайте шаблоны изображений UI элементов в папке `templates/`

## Использование

### Базовое использование

```python
from registration_bot import RegistrationBot

# Создаем бота с конфигурацией
bot = RegistrationBot(config_file="config.yaml")

# Запускаем массовую регистрацию
bot.run_batch_registration(max_accounts=10)

# Очистка ресурсов
bot.cleanup()
```

### Запуск из командной строки

```bash
cd registration_bot
python registration_bot.py
```

### Работа с отдельными модулями

#### Browser Automation

```python
from browser_automation import BrowserBot
from selenium.webdriver.common.by import By

with BrowserBot(headless=False, use_undetected=True) as bot:
    bot.navigate_to("https://example.com/register")
    bot.type_text(By.NAME, "username", "testuser")
    bot.type_text(By.NAME, "password", "SecurePass123!")
    bot.click_element(By.CSS_SELECTOR, "button[type='submit']")
```

#### Geelark Automation

```python
from geelark_automation import GeelarkBot

bot = GeelarkBot(emulator_window_title="Geelark")

# Поиск окна эмулятора
bot.locate_emulator_window()

# Последовательность действий
sequence = [
    {'action': 'click', 'x': 200, 'y': 400},
    {'action': 'type', 'text': 'test@example.com'},
    {'action': 'swipe', 'start_x': 200, 'start_y': 600, 'end_x': 200, 'end_y': 200},
]
bot.execute_sequence(sequence)
```

#### SMS Service

```python
from sms_service import SMSServiceManager, SMSServiceType

manager = SMSServiceManager(SMSServiceType.SMS_ACTIVATE, "YOUR_API_KEY")

# Получить номер и SMS код
result = manager.get_phone_and_code(service="go", country="ru", timeout=300)

if result:
    print(f"Телефон: {result['phone']}")
    print(f"SMS код: {result['code']}")
```

#### Data Manager

```python
from data_manager import DataManager

manager = DataManager("accounts.json")

# Получить следующий аккаунт
account = manager.get_next_account()

# Обновить статус
manager.update_account_status(account, 'success')

# Статистика
stats = manager.get_statistics()
print(stats)  # {'total': 10, 'pending': 5, 'success': 3, 'failed': 2}
```

## Настройка под свой сайт

Откройте `registration_bot.py` и модифицируйте методы:

### 1. `_register_in_browser()`

Замените логику на регистрацию для вашего сайта:

```python
def _register_in_browser(self, browser: BrowserBot, account: AccountData) -> bool:
    # Переход на страницу регистрации
    browser.navigate_to("https://yourwebsite.com/register")

    # Заполнение формы
    browser.type_text(By.NAME, "username", account.username)
    browser.type_text(By.NAME, "email", account.email)
    browser.type_text(By.NAME, "password", account.password)

    # Отправка формы
    browser.click_element(By.CSS_SELECTOR, "button[type='submit']")

    # Ожидание успеха
    return browser.wait_for_url_contains("success", timeout=10)
```

### 2. `_enter_sms_code()`

Адаптируйте под ваш сайт:

```python
def _enter_sms_code(self, browser: BrowserBot, code: str) -> bool:
    browser.type_text(By.NAME, "verification_code", code)
    browser.click_element(By.ID, "verify-button")
    return browser.wait_for_url_contains("verified", timeout=10)
```

### 3. `_configure_in_geelark()`

Добавьте действия в эмуляторе Android:

```python
def _configure_in_geelark(self, geelark: GeelarkBot, account: AccountData):
    sequence = [
        {'action': 'click', 'x': 200, 'y': 400},
        {'action': 'type', 'text': account.username},
        {'action': 'screenshot', 'filename': f'{account.username}_result.png'},
    ]
    geelark.execute_sequence(sequence)
```

## Создание шаблонов для Geelark

Для распознавания UI элементов в эмуляторе:

```python
from geelark_automation import GeelarkBot

bot = GeelarkBot()
bot.locate_emulator_window()

# Сохранить кнопку как шаблон
bot.save_template(x=100, y=200, width=150, height=50, template_name="login_button.png")

# Использовать шаблон
bot.click_image("login_button.png")
```

## Обработка ошибок

Бот автоматически обрабатывает ошибки и сохраняет статусы в файл данных:

- `pending` - ожидает обработки
- `in_progress` - в процессе регистрации
- `success` - успешно зарегистрирован
- `failed` - ошибка регистрации

Для повторной попытки неудачных регистраций:

```python
manager = DataManager("accounts.json")
manager.reset_failed_accounts()  # Сбросить failed → pending
```

## Советы по безопасности

1. **Не коммитьте API ключи** в Git:
   - Добавьте `config.yaml` в `.gitignore`
   - Используйте переменные окружения

2. **Соблюдайте Terms of Service** сервисов, на которых регистрируетесь

3. **Используйте задержки** между регистрациями:
   ```yaml
   registration:
     delay_between_accounts: 30  # секунд
   ```

4. **Headless режим** для работы на серверах:
   ```yaml
   browser:
     headless: true
   ```

## Поддерживаемые SMS сервисы

- **SMS-Activate** ([sms-activate.org](https://sms-activate.org/))
  - Поддержка множества сервисов
  - Низкие цены
  - API документация: [https://sms-activate.org/api](https://sms-activate.org/api)

- **5sim** ([5sim.net](https://5sim.net/))
  - Альтернативный сервис
  - Хорошая доступность номеров
  - API документация: [https://5sim.net/docs](https://5sim.net/docs)

## Временная почта

Бот поддерживает автоматическое создание временных email адресов:

```python
from sms_service import TempMailService

service = TempMailService()
email_data = service.create_email()
print(email_data['email'])  # random@tempmail.lol

# Получить сообщения
messages = service.get_messages(email_data['email'], timeout=60)
```

## Troubleshooting

### Браузер не запускается

- Установите ChromeDriver вручную
- Проверьте версию Chrome/Chromium
- Используйте `use_undetected: false` в конфиге

### Geelark окно не находится

На Windows установите `pygetwindow`:
```bash
pip install pygetwindow
```

Или установите регион вручную:
```python
bot.set_emulator_region(x=100, y=100, width=400, height=800)
```

### SMS коды не приходят

- Проверьте баланс аккаунта на сервисе
- Увеличьте `sms_timeout` в конфиге
- Проверьте правильность `service_code` для вашего сервиса

## Лицензия

Этот код предоставляется как есть для образовательных целей.
Используйте ответственно и соблюдайте законодательство и ToS сервисов.

## Поддержка

Для вопросов и предложений создайте issue в репозитории проекта.
