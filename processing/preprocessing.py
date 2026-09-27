def prepare_weather(weather: dict) -> dict:
    return {
        "temp_c": weather["temp_c"],
        "description": weather["description"],
        "warm_clothes": weather["temp_c"] < 0,
    }


def prepare_rates(currency: str, rate: float) -> dict:
    return {
        "currency": currency,
        "rate_to_rub": rate,
        "expensive": rate > 100,
    }