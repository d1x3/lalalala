# Betr Registration Bot

Автоматический бот для регистрации аккаунтов на https://picks.betr.app

## Возможности

- ✅ Автоматическая регистрация на Betr
- ✅ Интеграция с DaisySMS для получения SMS кодов
- ✅ Автоматическая генерация email и паролей
- ✅ Поддержка анти-детект браузеров (AdsPower, Dolphin Anty)
- ✅ Управление прокси и смена IP
- ✅ Отслеживание статусов регистрации
- ✅ Сохранение результатов в JSON/CSV

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Установите Chrome/Chromium браузер

3. Установите ChromeDriver (если используете обычный Chrome):
```bash
# Linux
sudo apt-get install chromium-chromedriver

# MacOS
brew install --cask chromedriver

# Windows
# Скачайте с https://chromedriver.chromium.org/
```

## Настройка

### 1. Подготовка данных

Создайте файл `betr_accounts.json` с данными аккаунтов:

```json
{
  "accounts": [
    {
      "first_name": "John",
      "last_name": "Smith",
      "date_of_birth": "1990-03-15",
      "address": "123 Main St, New York, NY 10001",
      "ssn_last4": "1234",
      "status": "pending"
    }
  ]
}
```

Или используйте CSV файл `betr_accounts.csv`:
```csv
first_name,last_name,date_of_birth,address,ssn_last4,status
John,Smith,1990-03-15,"123 Main St, New York, NY 10001",1234,pending
```

### 2. Настройка DaisySMS

1. Зарегистрируйтесь на https://daisysms.com
2. Пополните баланс
3. Получите API ключ в личном кабинете
4. Укажите ключ в `betr_registration_bot.py`:
```python
DAISY_API_KEY = "ВАШ_API_КЛЮЧ"
```

### 3. Настройка анти-детект браузера (опционально)

#### AdsPower

1. Установите AdsPower: https://www.adspower.net/
2. Создайте профили браузера
3. Запустите локальный API
4. В коде укажите ID профилей

#### Dolphin Anty

1. Установите Dolphin Anty: https://dolphin-anty.com/
2. Создайте профили
3. Получите API токен
4. В коде укажите токен и ID профилей

### 4. Настройка прокси (опционально)

Поддерживаемые провайдеры:
- Bright Data (Luminati)
- SmartProxy
- Proxy6.net
- Webshare.io
- Custom rotating proxy

## Использование

### Базовое использование

```bash
cd registration_bot
python betr_registration_bot.py
```

### Программное использование

```python
from betr_registration_bot import BetrRegistrationBot
from betr_data_manager import BetrDataManager

# Инициализация
DAISY_API_KEY = "ВАШ_API_КЛЮЧ"
bot = BetrRegistrationBot(DAISY_API_KEY, headless=False)
data_manager = BetrDataManager('betr_accounts.json')

# Получение аккаунта
account = data_manager.get_next_account()

# Инициализация браузера
bot.init_browser()

# Регистрация
success = bot.register_account(account)

# Обновление статуса
if success:
    data_manager.update_account_status(account, 'success')
else:
    data_manager.update_account_status(account, 'failed', 'Error message')

# Закрытие
bot.close_browser()
```

### С анти-детект браузером

```python
from antidetect_browser import create_browser_manager

# Создаем менеджер браузера
browser_manager = create_browser_manager(
    browser_type="adspower",
    api_url="http://local.adspower.net:50325"
)

# Открываем профиль
profile_id = "ваш_profile_id"
driver = browser_manager.get_selenium_driver(profile_id)

# Используйте driver для автоматизации
# ...

# Закрываем профиль
browser_manager.close_profile(profile_id)
```

### С управлением прокси

```python
from proxy_manager import create_proxy_manager

# Создаем менеджер прокси
proxy_manager = create_proxy_manager(
    provider="webshare",
    api_key="ВАШ_API_КЛЮЧ"
)

# Смена IP
proxy_manager.rotate_ip()

# Проверка текущего IP
current_ip = proxy_manager.get_current_ip()
print(f"Текущий IP: {current_ip}")
```

## Процесс регистрации

Бот выполняет следующие шаги:

1. Открывает https://picks.betr.app/picks/home/lobby
2. Разрешает доступ к геолокации
3. Нажимает Sign Up
4. Вводит email (генерируется) и пароль (генерируется)
5. Нажимает Next
6. Получает номер с DaisySMS для сервиса "betr"
7. Вводит номер телефона
8. Убирает галочку "enable biometrics"
9. Ставит галочку на соглашение с правилами
10. Нажимает Next
11. Получает SMS код с DaisySMS
12. Вводит SMS код
13. Вводит дату рождения (год, месяц, день)
14. Нажимает Apply, затем Next
15. Вводит последние 4 цифры SSN
16. Нажимает Next
17. Вводит имя и фамилию
18. Нажимает Next
19. Вводит адрес и выбирает из выпадающего списка
20. Нажимает Next
21. Проставляет 4 галки согласия
22. Нажимает Verify Identity
23. Проверяет результат регистрации

## Важные замечания

### ⚠️ Настройка селекторов

Файл `betr_registration_bot.py` содержит placeholder селекторы, помеченные комментариями `# TODO`.

**Вам нужно:**
1. Открыть сайт Betr в браузере
2. Использовать DevTools (F12) для поиска реальных селекторов
3. Заменить все `# TODO` селекторы на правильные

**Пример поиска селекторов:**
```python
# Вместо:
self.type_text(By.NAME, "email", account.email)  # TODO

# Найдите реальный селектор:
# 1. Откройте DevTools (F12)
# 2. Используйте инспектор (Ctrl+Shift+C)
# 3. Кликните на поле email
# 4. Скопируйте селектор (name, id, css selector, xpath)

# И замените:
self.type_text(By.ID, "email-input", account.email)
# или
self.type_text(By.CSS_SELECTOR, "input[data-testid='email']", account.email)
```

### Геолокация

Бот автоматически устанавливает геолокацию на Нью-Йорк:
```python
self.driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "accuracy": 100
})
```

Измените координаты если нужен другой штат.

### Статусы аккаунтов

- `pending` - ожидает обработки
- `in_progress` - в процессе регистрации
- `success` - успешно зарегистрирован
- `failed` - ошибка регистрации

## Структура файлов

```
registration_bot/
├── daisysms_service.py          # Интеграция с DaisySMS
├── betr_data_manager.py         # Управление данными Betr
├── betr_registration_bot.py     # Главный бот для Betr
├── antidetect_browser.py        # Работа с анти-детект браузерами
├── proxy_manager.py             # Управление прокси
├── betr_accounts.json           # Данные аккаунтов (создайте сами)
└── BETR_README.md              # Эта документация
```

## Troubleshooting

### Элемент не найден

**Проблема:** `TimeoutException: Element not found`

**Решение:**
1. Откройте Betr в браузере
2. Используйте DevTools для поиска правильного селектора
3. Замените селектор в коде
4. Увеличьте timeout если нужно:
```python
WebDriverWait(self.driver, 30)  # вместо 20
```

### SMS код не приходит

**Проблема:** Таймаут ожидания SMS

**Решение:**
1. Проверьте баланс на DaisySMS
2. Проверьте что сервис "betr" доступен
3. Увеличьте timeout:
```python
sms_code = self.daisy_sms.get_sms_code(activation_id, timeout=300)  # 5 минут
```

### Геолокация не работает

**Проблема:** Betr показывает ошибку геолокации

**Решение:**
1. Убедитесь что геолокация установлена перед открытием сайта
2. Используйте прокси из нужного штата
3. Проверьте координаты:
```python
# Пример для других штатов
# California: 34.0522, -118.2437
# Florida: 25.7617, -80.1918
# Texas: 29.7604, -95.3698
```

### Капча появляется

**Проблема:** Появляется капча при регистрации

**Решение:**
1. Используйте анти-детект браузер
2. Используйте residential прокси
3. Добавьте случайные задержки
4. Меняйте IP после каждой попытки

## DaisySMS - Поддерживаемые страны

Для Betr (США) используйте код страны: `12`

Другие коды стран см. в документации: https://daisysms.com/docs/api

## Безопасность

1. **Не коммитьте API ключи** в Git
2. **Используйте .gitignore** для конфиденциальных файлов
3. **Соблюдайте ToS** сервисов
4. **Используйте задержки** между регистрациями
5. **Меняйте IP** после каждой попытки

## Поддержка

Для вопросов и помощи с настройкой селекторов создайте issue в репозитории.

## Лицензия

Этот код предоставляется как есть для образовательных целей.
Используйте ответственно и соблюдайте законодательство.
