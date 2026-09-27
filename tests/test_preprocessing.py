import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import Mock, patch

import requests

from clients.http import CityNotFound, CurrencyNotFound, ServiceUnavailable, get_json
from clients.rates import get_rate
from clients.weather import get_weather
from main import main
from processing.preprocessing import prepare_rates, prepare_weather


def response(status, payload=None, headers=None):
    result = Mock(status_code=status, headers=headers or {})
    result.json.return_value = payload
    return result


class PreprocessingTests(unittest.TestCase):
    def test_thresholds(self):
        self.assertTrue(prepare_weather({"temp_c": -0.1, "description": "snow"})["warm_clothes"])
        self.assertFalse(prepare_weather({"temp_c": 0, "description": "clear sky"})["warm_clothes"])
        self.assertFalse(prepare_rates("USD", 100)["expensive"])
        self.assertTrue(prepare_rates("EUR", 100.01)["expensive"])


class HttpTests(unittest.TestCase):

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_timeout_connection_then_success(self, get, sleep):
        get.side_effect = [requests.exceptions.Timeout(), requests.exceptions.ConnectionError(), response(200, {"ok": 1})]
        self.assertEqual(get_json("https://example.test")[1], {"ok": 1})
        self.assertEqual(get.call_count, 3)
        self.assertTrue(all(call.kwargs["timeout"] <= 10 for call in get.call_args_list))
        self.assertEqual(sleep.call_count, 2)

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_temporary_server_error_exhausted(self, get, sleep):
        get.side_effect = [response(s) for s in (500, 502, 504)]
        with self.assertRaises(ServiceUnavailable):
            get_json("https://example.test")
        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_retry_after_numeric(self, get, sleep):
        get.side_effect = [response(429, headers={"Retry-After": "2"}), response(200, {"ok": True})]
        get_json("https://example.test")
        sleep.assert_called_once_with(2.0)

    @patch("clients.http.requests.get")
    def test_invalid_json(self, get):
        bad = response(200)
        bad.json.side_effect = ValueError("bad JSON")
        get.return_value = bad
        with self.assertRaises(ServiceUnavailable):
            get_json("https://example.test")


class ClientTests(unittest.TestCase):

    @patch("clients.weather.get_json")
    def test_weather_two_requests(self, fetch):
        fetch.side_effect = [(200, {"results": [{"latitude": 55.75, "longitude": 37.61}]}),
                             (200, {"current": {"temperature_2m": -3.2, "weather_code": 0}})]
        self.assertEqual(get_weather("Moscow"), {"temp_c": -3.2, "description": "clear sky"})
        self.assertEqual(fetch.call_count, 2)

    @patch("clients.weather.get_json", return_value=(200, {}))
    def test_unknown_city(self, fetch):
        with self.assertRaises(CityNotFound):
            get_weather("NoSuchCity")

    @patch("clients.rates.get_json", return_value=(200, {"base": "USD", "quote": "RUB", "rate": 92.15}))
    def test_rate(self, fetch):
        self.assertEqual(get_rate("USD"), 92.15)

    @patch("clients.rates.get_json", return_value=(422, None))
    def test_unknown_currency(self, fetch):
        with self.assertRaises(CurrencyNotFound):
            get_rate("ZZZ")

    @patch("clients.rates.get_json", return_value=(200, {"base": "USD", "quote": "RUB", "rate": "92"}))
    def test_malformed_rate(self, fetch):
        with self.assertRaises(ServiceUnavailable):
            get_rate("USD")


class CliTests(unittest.TestCase):

    @patch("main.build_city_summary", return_value={"city": "Moscow", "weather": {"temp_c": -1.0, "description": "snow", "warm_clothes": True},
                                                    "rates": {"currency": "USD", "rate_to_rub": 92.15, "expensive": False}})
    def test_json_output(self, build):
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["--city", "Moscow", "--json"]), 0)
        self.assertIn('"warm_clothes": true', output.getvalue())
        build.assert_called_once_with("Moscow", "USD")

    def test_bad_currency_argument(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                main(["--city", "Moscow", "--currency", "DOLLAR"])
        self.assertEqual(error.exception.code, 2)

    @patch("main.build_city_summary", side_effect=CurrencyNotFound("ZZZ"))
    def test_unknown_currency_exit_code(self, build):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--city", "Moscow", "--currency", "ZZZ"]), 3)

    @patch("main.build_city_summary", side_effect=ServiceUnavailable("offline"))
    def test_service_failure_exit_code(self, build):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--city", "Moscow"]), 4)


if __name__ == "__main__":
    unittest.main()