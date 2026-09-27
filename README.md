# Сводка по городу

CLI показывает текущую температуру и курс выбранной валюты к рублю. Используются бесплатные HTTP GET API Open-Meteo (геокодинг → текущая погода) и Frankfurter v2

## Файлы

```text
city_summary/
├── main.py
├── requirements.txt
├── README.md
├── clients/
│   ├── __init__.py
│   ├── http.py
│   ├── weather.py
│   └── rates.py
├── processing/
│   ├── __init__.py
│   ├── preprocessing.py
│   └── service.py
└── tests/
    └── test_preprocessing.py
```

Все команды ниже выполняются из папки `city_summary`. Python 3.9+

## Установка и запуск

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python main.py --city Moscow
python main.py --city Moscow --currency EUR
python main.py --city Moscow --json
python -m unittest discover -s tests -v
```

Пример формата вывода (значения зависят от ответов API):

```text
Город: Moscow
Погода: -3.2°C, clear sky
Тёплая одежда: да
USD→RUB: 92.15
Дорогой курс: нет
```

JSON-формат содержит `city`, `weather` (`temp_c`, `description`, `warm_clothes`) и `rates` (`currency`, `rate_to_rub`, `expensive`)

## Правила

- `warm_clothes = true`, если температура строго ниже 0°C
- `expensive = true`, если курс строго выше 100 RUB за единицу валюты

## API

- Open-Meteo geocoding: https://open-meteo.com/en/docs/geocoding-api
- Open-Meteo forecast: https://open-meteo.com/en/docs
- Frankfurter v2: https://frankfurter.dev/