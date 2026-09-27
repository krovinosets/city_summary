import math

from clients.http import CurrencyNotFound, ServiceUnavailable, get_json

RATE_URL = "https://api.frankfurter.dev/v2/rate/{}/RUB"


def get_rate(currency: str) -> float:
    url = RATE_URL.format(currency)
    status, data = get_json(url, not_found_statuses=(404, 422))
    if status in (404, 422):
        raise CurrencyNotFound(
            f"код валюты «{currency}» или пара {currency}/RUB не найдены"
        )
    if not isinstance(data, dict):
        raise ServiceUnavailable("Frankfurter: ответ должен быть JSON-объектом")
    base, quote = data.get("base"), data.get("quote")
    if (
        not isinstance(base, str)
        or not isinstance(quote, str)
        or base.upper() != currency
        or quote.upper() != "RUB"
    ):
        raise ServiceUnavailable("Frankfurter: ответ относится к другой валютной паре")
    rate = data.get("rate")
    if (
        isinstance(rate, bool)
        or not isinstance(rate, (int, float))
        or not math.isfinite(rate)
        or rate <= 0
    ):
        raise ServiceUnavailable(
            "Frankfurter: отсутствует корректное положительное поле rate"
        )
    return float(rate)
