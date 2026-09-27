import argparse
import json
import re
import sys

from clients.http import CityNotFound, CurrencyNotFound, ServiceUnavailable
from processing.service import build_city_summary


def nonempty_city(value: str) -> str:
    value = value.strip()
    if not value:
        raise argparse.ArgumentTypeError("город не может быть пустым")
    return value


def currency_code(value: str) -> str:
    value = value.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", value):
        raise argparse.ArgumentTypeError(
            "код валюты должен состоять из трёх латинских букв"
        )
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Погода в городе и курс валюты к рублю"
    )
    parser.add_argument(
        "--city", required=True, type=nonempty_city, help="Название города"
    )
    parser.add_argument(
        "--currency",
        default="USD",
        type=currency_code,
        help="Трёхбуквенный код валюты (по умолчанию USD)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Вывести сводку в формате JSON"
    )
    args = parser.parse_args(argv)

    try:
        summary = build_city_summary(args.city, args.currency)
    except (CityNotFound, CurrencyNotFound) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 3
    except ServiceUnavailable as exc:
        print(f"Ошибка внешнего сервиса: {exc}", file=sys.stderr)
        return 4

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        weather = summary["weather"]
        rates = summary["rates"]
        print(f"Город: {summary['city']}")
        print(f"Погода: {weather['temp_c']:.1f}°C, {weather['description']}")
        print(f"Тёплая одежда: {'да' if weather['warm_clothes'] else 'нет'}")
        print(f"{rates['currency']}→RUB: {rates['rate_to_rub']:.2f}")
        print(f"Дорогой курс: {'да' if rates['expensive'] else 'нет'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
