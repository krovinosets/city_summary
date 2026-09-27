import math
import time

import requests

TIMEOUT = 5  # seconds per request, not a total deadline
RETRIES = 2  # two retries after the first attempt
RETRYABLE_STATUSES = {500, 502, 503, 504}
MAX_RETRY_AFTER = 30  # avoid unbounded waits from server-controlled headers


class CityNotFound(Exception):
    """No geocoding match for the requested city."""


class CurrencyNotFound(Exception):
    """Currency or currency pair is not available."""


class ServiceUnavailable(Exception):
    """External API failed or returned an unusable response."""


def get_json(url: str, *, params=None, not_found_statuses=()):
    """Return decoded JSON; optionally leave specified statuses to the caller.

    Never retry an ordinary 4xx error. Retry timeouts, connection errors,
    temporary 5xx and 429 at most RETRIES times.
    """
    for attempt in range(RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=TIMEOUT)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            if attempt == RETRIES:
                raise ServiceUnavailable(f"нет связи с {url} после {RETRIES + 1} попыток") from exc
            time.sleep(0.5 * (2 ** attempt))
            continue
        except requests.exceptions.RequestException as exc:
            raise ServiceUnavailable(f"не удалось запросить {url}") from exc

        status = response.status_code
        if status == 429 or status in RETRYABLE_STATUSES:
            if attempt == RETRIES:
                raise ServiceUnavailable(f"{url}: HTTP {status} после {RETRIES + 1} попыток")
            delay = 0.5 * (2 ** attempt)
            if status == 429:
                raw = response.headers.get("Retry-After", "")
                try:
                    seconds = float(raw)
                    if math.isfinite(seconds) and seconds >= 0:
                        if seconds > MAX_RETRY_AFTER:
                            raise ServiceUnavailable(
                                f"{url}: Retry-After {seconds:g} с превышает лимит ожидания {MAX_RETRY_AFTER} с"
                            )
                        delay = seconds
                except ValueError:
                    pass  # HTTP-date or malformed header: use short backoff
            time.sleep(delay)
            continue

        if status not in not_found_statuses and not 200 <= status < 300:
            raise ServiceUnavailable(f"{url}: HTTP {status}")
        if status in not_found_statuses:
            return status, None
        try:
            return status, response.json()
        except (ValueError, requests.exceptions.RequestException) as exc:
            raise ServiceUnavailable(f"{url}: ответ не является корректным JSON") from exc

    raise AssertionError("retry loop should always return or raise")