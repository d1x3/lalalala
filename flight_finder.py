"""
Модуль для поиска дешевых авиабилетов
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import flight_config as config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlightFinder:
    """Класс для поиска авиабилетов"""

    def __init__(self):
        self.aviasales_api_base = "https://api.travelpayouts.com/aviasales/v3"
        # Альтернативный API (не требует токена для некоторых запросов)
        self.aviasales_data_api = "https://www.travelpayouts.com/data/flights.json"

    def search_flights(self, origin: str, destination: str, date: str) -> List[Dict]:
        """
        Поиск билетов на указанную дату

        Args:
            origin: Код города отправления (IATA)
            destination: Код города назначения (IATA)
            date: Дата в формате YYYY-MM-DD

        Returns:
            Список найденных билетов
        """
        flights = []

        # Пробуем несколько источников
        try:
            # Метод 1: Aviasales Latest Prices API (не требует токена)
            flights.extend(self._search_aviasales_latest(origin, destination, date))
        except Exception as e:
            logger.warning(f"Ошибка при поиске через Aviasales Latest: {e}")

        try:
            # Метод 2: Прямой поиск через Aviasales
            flights.extend(self._search_aviasales_direct(origin, destination, date))
        except Exception as e:
            logger.warning(f"Ошибка при прямом поиске Aviasales: {e}")

        return flights

    def _search_aviasales_latest(self, origin: str, destination: str, date: str) -> List[Dict]:
        """Поиск через Aviasales Latest Prices API"""
        url = f"https://api.travelpayouts.com/v2/prices/latest"

        params = {
            'origin': origin,
            'destination': destination,
            'beginning_of_period': date,
            'period_type': 'day',
            'one_way': 'true',
            'currency': 'rub',
            'limit': 30,
            'page': 1,
            'sorting': 'price'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            flights = []
            if data.get('success') and data.get('data'):
                for flight_data in data['data']:
                    flight = self._parse_aviasales_flight(flight_data)
                    if flight:
                        flights.append(flight)

            return flights
        except Exception as e:
            logger.error(f"Ошибка _search_aviasales_latest: {e}")
            return []

    def _search_aviasales_direct(self, origin: str, destination: str, date: str) -> List[Dict]:
        """Прямой поиск через поисковик Aviasales"""
        # Формируем URL для поиска
        search_url = f"https://www.aviasales.ru/search/{origin}{date}{destination}1"

        # Используем API для получения минимальных цен
        api_url = "https://www.aviasales.com/search_api/prices"

        params = {
            'origin_iata': origin,
            'destination_iata': destination,
            'departure_at': date,
            'return_at': '',
            'one_way': 'true',
            'currency': 'rub'
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = requests.get(api_url, params=params, headers=headers, timeout=15)
            if response.status_code == 200:
                # Парсим ответ
                data = response.json()
                flights = []

                # Обрабатываем данные (структура может варьироваться)
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict) and 'price' in value:
                            flight = {
                                'origin': origin,
                                'destination': destination,
                                'departure_date': date,
                                'price': value.get('price', 0),
                                'currency': 'RUB',
                                'airline': value.get('airline', 'Unknown'),
                                'search_url': search_url
                            }
                            flights.append(flight)

                return flights
        except Exception as e:
            logger.error(f"Ошибка _search_aviasales_direct: {e}")

        return []

    def _parse_aviasales_flight(self, flight_data: Dict) -> Optional[Dict]:
        """Парсинг данных о рейсе от Aviasales"""
        try:
            price = flight_data.get('value') or flight_data.get('price', 0)

            flight = {
                'origin': flight_data.get('origin', config.ORIGIN_CITY),
                'destination': flight_data.get('destination', config.DESTINATION_CITY),
                'departure_date': flight_data.get('departure_at', ''),
                'return_date': flight_data.get('return_at'),
                'price': price,
                'currency': 'RUB',
                'airline': flight_data.get('airline', 'Unknown'),
                'flight_number': flight_data.get('flight_number', ''),
                'transfers': flight_data.get('transfers', 0),
                'link': flight_data.get('link', ''),
                'found_at': datetime.now().isoformat()
            }

            return flight
        except Exception as e:
            logger.error(f"Ошибка парсинга рейса: {e}")
            return None

    def filter_by_price(self, flights: List[Dict], max_price: float) -> List[Dict]:
        """Фильтрация билетов по цене"""
        return [f for f in flights if f.get('price', float('inf')) <= max_price]

    def filter_by_time(self, flights: List[Dict], date_config: Dict) -> List[Dict]:
        """Фильтрация билетов по времени вылета"""
        if date_config.get('time_preference') == 'any':
            return flights

        filtered = []
        min_hour = date_config.get('min_hour', 0)
        max_hour = date_config.get('max_hour', 23)

        for flight in flights:
            departure = flight.get('departure_date', '')
            if not departure:
                continue

            try:
                # Парсим дату и время
                if 'T' in departure:
                    dt = datetime.fromisoformat(departure.replace('Z', '+00:00'))
                    hour = dt.hour

                    if min_hour <= hour <= max_hour:
                        filtered.append(flight)
                else:
                    # Если нет времени, включаем рейс
                    filtered.append(flight)
            except Exception as e:
                logger.warning(f"Ошибка парсинга времени {departure}: {e}")
                # В случае ошибки включаем рейс
                filtered.append(flight)

        return filtered if filtered else flights

    def search_all_dates(self) -> List[Dict]:
        """Поиск билетов на все указанные даты"""
        all_flights = []

        for date_config in config.DEPARTURE_DATES:
            date = date_config['date']
            logger.info(f"Поиск билетов на {date}...")

            flights = self.search_flights(
                config.ORIGIN_CITY,
                config.DESTINATION_CITY,
                date
            )

            # Фильтруем по цене
            flights = self.filter_by_price(flights, config.MAX_PRICE)

            # Фильтруем по времени
            flights = self.filter_by_time(flights, date_config)

            logger.info(f"Найдено {len(flights)} подходящих билетов на {date}")
            all_flights.extend(flights)

        return all_flights

    def deduplicate_flights(self, flights: List[Dict]) -> List[Dict]:
        """Удаление дубликатов билетов"""
        seen = set()
        unique_flights = []

        for flight in flights:
            # Создаем уникальный ключ
            key = (
                flight.get('origin'),
                flight.get('destination'),
                flight.get('departure_date'),
                flight.get('price'),
                flight.get('airline')
            )

            if key not in seen:
                seen.add(key)
                unique_flights.append(flight)

        return unique_flights


def format_flight_message(flight: Dict) -> str:
    """Форматирование сообщения о билете для Telegram"""
    origin = flight.get('origin', 'MOW')
    destination = flight.get('destination', 'UFA')
    date = flight.get('departure_date', '')
    price = flight.get('price', 0)
    airline = flight.get('airline', 'Unknown')
    transfers = flight.get('transfers', 0)

    # Форматируем дату
    try:
        if 'T' in date:
            dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
            formatted_date = dt.strftime('%d.%m.%Y %H:%M')
        else:
            dt = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = dt.strftime('%d.%m.%Y')
    except:
        formatted_date = date

    # Формируем ссылку для поиска
    search_url = flight.get('link') or flight.get('search_url')
    if not search_url:
        search_url = f"https://www.aviasales.ru/search/{origin}{date.split('T')[0]}{destination}1"

    message = f"✈️ Дешевый билет найден!\n\n"
    message += f"📍 Маршрут: {origin} → {destination}\n"
    message += f"📅 Дата: {formatted_date}\n"
    message += f"💰 Цена: {price:,.0f} ₽\n"
    message += f"🏢 Авиакомпания: {airline}\n"

    if transfers == 0:
        message += f"🎯 Прямой рейс\n"
    else:
        message += f"🔄 Пересадок: {transfers}\n"

    message += f"\n🔗 Поиск: {search_url}"

    return message
