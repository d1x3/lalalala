#!/usr/bin/env python3
"""
Тестовый скрипт для проверки ответа API Aviasales
"""

import requests
import json
import sys
sys.path.insert(0, '/home/user/lalalala')
import flight_config as config

print("=" * 80)
print("ТЕСТ: Проверка ответа API Aviasales")
print("=" * 80)

url = "https://api.travelpayouts.com/v2/prices/latest"

params = {
    'origin': 'MOW',
    'destination': 'UFA',
    'beginning_of_period': '2025-12-26',
    'period_type': 'day',
    'one_way': 'true',
    'currency': 'rub',
    'limit': 3,
    'page': 1,
    'sorting': 'price',
    'token': config.AVIASALES_API_TOKEN
}

print(f"\nЗапрос к API:")
print(f"URL: {url}")
print(f"Параметры: {json.dumps(params, indent=2, ensure_ascii=False)}")
print("\n" + "=" * 80)

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"Статус ответа: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\nСтруктура ответа:")
        print(f"  success: {data.get('success')}")
        print(f"  currency: {data.get('currency')}")
        print(f"  data: {type(data.get('data'))}")

        if data.get('data'):
            print(f"\nКоличество билетов: {len(data['data'])}")
            print(f"\nПервый билет (полные данные):")
            print(json.dumps(data['data'][0], indent=2, ensure_ascii=False))

            print(f"\nВсе билеты (краткая информация):")
            for i, flight in enumerate(data['data'][:3], 1):
                print(f"\nБилет #{i}:")
                print(f"  Доступные поля: {list(flight.keys())}")
                print(f"  origin: {flight.get('origin')}")
                print(f"  destination: {flight.get('destination')}")
                print(f"  departure_at: {flight.get('departure_at')}")
                print(f"  depart_date: {flight.get('depart_date')}")
                print(f"  price/value: {flight.get('price')} / {flight.get('value')}")
                print(f"  airline: {flight.get('airline')}")
        else:
            print("\nНет данных о билетах")
    else:
        print(f"Ошибка: {response.text}")

except Exception as e:
    print(f"Исключение: {e}")

print("\n" + "=" * 80)
print("Тест завершен")
print("=" * 80)
