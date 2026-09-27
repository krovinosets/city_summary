from clients.rates import get_rate
from clients.weather import get_weather
from processing.preprocessing import prepare_rates, prepare_weather


def build_city_summary(city: str, currency: str = "USD") -> dict:
    return {
        "city": city,
        "weather": prepare_weather(get_weather(city)),
        "rates": prepare_rates(currency, get_rate(currency)),
    }