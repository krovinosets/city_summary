import math

from clients.http import CityNotFound, ServiceUnavailable, get_json

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snowfall",
    73: "moderate snowfall",
    75: "heavy snowfall",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    97: "heavy thunderstorm",
    99: "thunderstorm with heavy hail",
}


def finite_number(value, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ServiceUnavailable(f"Open-Meteo: неверное поле {label}")
    return float(value)


def get_weather(city: str) -> dict:
    _, places = get_json(GEOCODE_URL, params={"name": city, "count": 1})
    if not isinstance(places, dict):
        raise ServiceUnavailable("Open-Meteo: неверный формат ответа геокодинга")
    results = places.get("results")
    if results is None and places.get("error") is not True:
        raise CityNotFound(f"город «{city}» не найден")
    if not isinstance(results, list):
        raise ServiceUnavailable("Open-Meteo: неверное поле results")
    if not results:
        raise CityNotFound(f"город «{city}» не найден")
    place = results[0]
    if not isinstance(place, dict):
        raise ServiceUnavailable("Open-Meteo: неверный результат геокодинга")
    latitude = finite_number(place.get("latitude"), "latitude")
    longitude = finite_number(place.get("longitude"), "longitude")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ServiceUnavailable("Open-Meteo: координаты вне допустимого диапазона")

    _, forecast = get_json(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code",
            "temperature_unit": "celsius",
        },
    )
    if not isinstance(forecast, dict) or not isinstance(forecast.get("current"), dict):
        raise ServiceUnavailable("Open-Meteo: отсутствует объект current")
    current = forecast["current"]
    temperature = finite_number(current.get("temperature_2m"), "temperature_2m")
    code = current.get("weather_code")
    if isinstance(code, bool) or not isinstance(code, int):
        raise ServiceUnavailable("Open-Meteo: неверное поле weather_code")
    return {
        "temp_c": temperature,
        "description": WEATHER_CODES.get(code, f"weather code {code}"),
    }
