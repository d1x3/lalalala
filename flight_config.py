"""
Конфигурация для бота поиска авиабилетов
"""

# Telegram Bot настройки
TELEGRAM_BOT_TOKEN = "8080110045:AAGK01_8PByIWA-F9o4wJnlGRdQtWu89Uyo"
TELEGRAM_CHAT_ID = None  # Будет заполнено автоматически при первом запуске

# Aviasales API настройки
AVIASALES_API_TOKEN = "d466c02eb95b443bda5583c851f210ce"

# Настройки поиска билетов
ORIGIN_CITY = "MOW"  # Москва (код IATA)
DESTINATION_CITY = "UFA"  # Уфа (код IATA)
MAX_PRICE = 20000  # Максимальная цена билета в рублях

# Даты вылета
DEPARTURE_DATES = [
    {
        "date": "2024-12-26",
        "time_preference": "evening",  # вечер
        "min_hour": 18,  # с 18:00
        "max_hour": 23   # до 23:59
    },
    {
        "date": "2024-12-27",
        "time_preference": "any",  # любое время
        "min_hour": 0,
        "max_hour": 23
    },
    {
        "date": "2024-12-28",
        "time_preference": "any",  # любое время
        "min_hour": 0,
        "max_hour": 23
    }
]

# Интервал проверки (в секундах)
CHECK_INTERVAL = 3600  # Проверять каждый час

# Файл для хранения найденных билетов (чтобы не отправлять дубликаты)
FOUND_FLIGHTS_FILE = "found_flights.json"
