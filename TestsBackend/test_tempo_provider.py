import unittest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

current_directory = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_directory, "../Backend")
sys.path.insert(0, backend_path)

from Backend.tempo_provider import TempoProvider, DayPrice, DayStatus


class TempoProviderTestCase(unittest.TestCase):
    """Test suite for TempoProvider class"""

    def setUp(self):
        """Set up test fixtures"""
        self.provider = TempoProvider()

    def test_map_code_to_price_low(self):
        """Test mapping codeJour 1 to LOW price"""
        result = self.provider._map_code_to_price(1)
        self.assertEqual(result, DayPrice.LOW)

    def test_map_code_to_price_normal(self):
        """Test mapping codeJour 2 to NORMAL price"""
        result = self.provider._map_code_to_price(2)
        self.assertEqual(result, DayPrice.NORMAL)

    def test_map_code_to_price_high(self):
        """Test mapping codeJour 3 to HIGH price"""
        result = self.provider._map_code_to_price(3)
        self.assertEqual(result, DayPrice.HIGH)

    def test_map_code_to_price_unknown(self):
        """Test mapping codeJour 0 or invalid to UNKNOWN price"""
        self.assertEqual(self.provider._map_code_to_price(0), DayPrice.UNKNOWN)
        self.assertEqual(self.provider._map_code_to_price(4), DayPrice.UNKNOWN)
        self.assertEqual(self.provider._map_code_to_price(-1), DayPrice.UNKNOWN)

    @patch('Backend.tempo_provider.requests.get')
    def test_fetch_tempo_day_success(self, mock_get):
        """Test successful API call to fetch Tempo day data"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "dateJour": "2026-01-06",
            "codeJour": 3,
            "periode": "2025-2026",
            "libCouleur": "Rouge"
        }
        mock_get.return_value = mock_response

        result = self.provider._fetch_tempo_day("today")

        self.assertIsNotNone(result)
        self.assertEqual(result["codeJour"], 3)
        self.assertEqual(result["libCouleur"], "Rouge")
        mock_get.assert_called_once_with(
            "https://www.api-couleur-tempo.fr/api/jourTempo/today",
            timeout=10
        )

    @patch('Backend.tempo_provider.requests.get')
    def test_fetch_tempo_day_http_error(self, mock_get):
        """Test handling of HTTP error during API call"""
        mock_get.side_effect = Exception("Connection error")

        result = self.provider._fetch_tempo_day("today")

        self.assertIsNone(result)

    @patch('Backend.tempo_provider.requests.get')
    def test_fetch_tempo_day_json_error(self, mock_get):
        """Test handling of JSON parsing error"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        result = self.provider._fetch_tempo_day("today")

        self.assertIsNone(result)

    @patch('Backend.tempo_provider.requests.get')
    def test_update_success(self, mock_get):
        """Test successful update of both today and tomorrow data"""
        today_response = MagicMock()
        today_response.status_code = 200
        today_response.json.return_value = {
            "dateJour": "2026-01-06",
            "codeJour": 3,
            "periode": "2025-2026",
            "libCouleur": "Rouge"
        }

        tomorrow_response = MagicMock()
        tomorrow_response.status_code = 200
        tomorrow_response.json.return_value = {
            "dateJour": "2026-01-07",
            "codeJour": 1,
            "periode": "2025-2026",
            "libCouleur": "Bleu"
        }

        mock_get.side_effect = [today_response, tomorrow_response]

        self.provider.update()

        self.assertEqual(self.provider.get_today_price(), DayPrice.HIGH)
        self.assertEqual(self.provider.get_tomorrow_price(), DayPrice.LOW)
        self.assertIsNotNone(self.provider.get_today_data())
        self.assertIsNotNone(self.provider.get_tomorrow_data())
        self.assertEqual(mock_get.call_count, 2)

    @patch('Backend.tempo_provider.requests.get')
    def test_update_today_failure(self, mock_get):
        """Test update when today's API call fails"""
        mock_get.side_effect = Exception("Connection error")

        self.provider.update()

        self.assertEqual(self.provider.get_today_price(), DayPrice.UNKNOWN)
        self.assertEqual(self.provider.get_tomorrow_price(), DayPrice.UNKNOWN)

    @patch('Backend.tempo_provider.requests.get')
    def test_update_tomorrow_failure(self, mock_get):
        """Test update when only tomorrow's API call fails"""
        today_response = MagicMock()
        today_response.status_code = 200
        today_response.json.return_value = {
            "dateJour": "2026-01-06",
            "codeJour": 2,
            "periode": "2025-2026",
            "libCouleur": "Blanc"
        }

        mock_get.side_effect = [today_response, Exception("Connection error")]

        self.provider.update()

        self.assertEqual(self.provider.get_today_price(), DayPrice.NORMAL)
        self.assertEqual(self.provider.get_tomorrow_price(), DayPrice.UNKNOWN)

    def test_initial_state(self):
        """Test that provider initializes with UNKNOWN prices"""
        provider = TempoProvider()
        self.assertEqual(provider.get_today_price(), DayPrice.UNKNOWN)
        self.assertEqual(provider.get_tomorrow_price(), DayPrice.UNKNOWN)
        self.assertIsNone(provider.get_today_data())
        self.assertIsNone(provider.get_tomorrow_data())

    @patch('Backend.tempo_provider.requests.get')
    def test_all_price_levels(self, mock_get):
        """Test all three price levels can be properly fetched and stored"""
        # Test Blue (Low)
        blue_response = MagicMock()
        blue_response.status_code = 200
        blue_response.json.return_value = {"codeJour": 1, "libCouleur": "Bleu"}

        white_response = MagicMock()
        white_response.status_code = 200
        white_response.json.return_value = {"codeJour": 2, "libCouleur": "Blanc"}

        mock_get.side_effect = [blue_response, white_response]

        self.provider.update()
        self.assertEqual(self.provider.get_today_price(), DayPrice.LOW)
        self.assertEqual(self.provider.get_tomorrow_price(), DayPrice.NORMAL)

    @patch('Backend.tempo_provider.requests.get')
    def test_consecutive_updates(self, mock_get):
        """Test that consecutive updates properly overwrite previous data"""
        # First update
        first_today = MagicMock()
        first_today.status_code = 200
        first_today.json.return_value = {"codeJour": 1, "libCouleur": "Bleu"}

        first_tomorrow = MagicMock()
        first_tomorrow.status_code = 200
        first_tomorrow.json.return_value = {"codeJour": 2, "libCouleur": "Blanc"}

        # Second update
        second_today = MagicMock()
        second_today.status_code = 200
        second_today.json.return_value = {"codeJour": 3, "libCouleur": "Rouge"}

        second_tomorrow = MagicMock()
        second_tomorrow.status_code = 200
        second_tomorrow.json.return_value = {"codeJour": 1, "libCouleur": "Bleu"}

        mock_get.side_effect = [first_today, first_tomorrow, second_today, second_tomorrow]

        # First update
        self.provider.update()
        self.assertEqual(self.provider.get_today_price(), DayPrice.LOW)
        self.assertEqual(self.provider.get_tomorrow_price(), DayPrice.NORMAL)

        # Second update
        self.provider.update()
        self.assertEqual(self.provider.get_today_price(), DayPrice.HIGH)
        self.assertEqual(self.provider.get_tomorrow_price(), DayPrice.LOW)


class TempoStatusTestCase(unittest.TestCase):
    """Status and freshness reporting : an UNKNOWN colour must say why."""

    def setUp(self):
        self.provider = TempoProvider()

    @staticmethod
    def _response(code_day):
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"codeJour": code_day}
        return response

    def test_status_never_fetched_before_any_update(self):
        self.assertEqual(self.provider.get_today_status(), DayStatus.NEVER_FETCHED)
        self.assertEqual(self.provider.get_tomorrow_status(), DayStatus.NEVER_FETCHED)
        self.assertIsNone(self.provider.get_last_success())
        self.assertTrue(self.provider.is_stale())

    @patch('Backend.tempo_provider.requests.get')
    def test_status_ok_when_published(self, mock_get):
        mock_get.side_effect = [self._response(3), self._response(1)]

        self.provider.update()

        self.assertEqual(self.provider.get_today_status(), DayStatus.OK)
        self.assertEqual(self.provider.get_tomorrow_status(), DayStatus.OK)
        self.assertIsNotNone(self.provider.get_last_success())
        self.assertFalse(self.provider.is_stale())

    @patch('Backend.tempo_provider.requests.get')
    def test_code_zero_reported_as_not_published(self, mock_get):
        """codeJour 0 is EDF not having published yet, not a failure."""
        mock_get.side_effect = [self._response(1), self._response(0)]

        self.provider.update()

        self.assertEqual(self.provider.get_tomorrow_price(), DayPrice.UNKNOWN)
        self.assertEqual(self.provider.get_tomorrow_status(), DayStatus.NOT_PUBLISHED)
        # Reaching the API at all still counts as a successful refresh.
        self.assertIsNotNone(self.provider.get_last_success())

    @patch('Backend.tempo_provider.requests.get')
    def test_network_failure_reported_as_fetch_error(self, mock_get):
        mock_get.side_effect = Exception("Connection error")

        self.provider.update()

        self.assertEqual(self.provider.get_today_status(), DayStatus.FETCH_ERROR)
        self.assertEqual(self.provider.get_tomorrow_status(), DayStatus.FETCH_ERROR)
        self.assertIsNone(self.provider.get_last_success())

    @patch('Backend.tempo_provider.requests.get')
    def test_unexpected_code_reported_as_fetch_error(self, mock_get):
        mock_get.side_effect = [self._response(42), self._response(1)]

        self.provider.update()

        self.assertEqual(self.provider.get_today_price(), DayPrice.UNKNOWN)
        self.assertEqual(self.provider.get_today_status(), DayStatus.FETCH_ERROR)

    @patch('Backend.tempo_provider.requests.get')
    def test_non_dict_payload_does_not_raise(self, mock_get):
        """A JSON list used to crash update() on .get and kill the refresh loop."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = [{"codeJour": 1}]
        mock_get.return_value = response

        self.provider.update()

        self.assertEqual(self.provider.get_today_status(), DayStatus.FETCH_ERROR)
        self.assertEqual(self.provider.get_today_price(), DayPrice.UNKNOWN)

    @patch('Backend.tempo_provider.requests.get')
    def test_outdated_colour_reported_as_stale(self, mock_get):
        provider = TempoProvider(stale_after_s=60)
        mock_get.side_effect = [self._response(3), self._response(3)]
        provider.update()
        self.assertEqual(provider.get_today_price(), DayPrice.HIGH)

        # Pretend the last successful call happened well beyond the trust window.
        provider._last_success = datetime.now() - timedelta(seconds=600)

        self.assertTrue(provider.is_stale())
        self.assertEqual(provider.get_today_status(), DayStatus.STALE)
        # A colour we cannot vouch for must not drive the heating any more.
        self.assertEqual(provider.get_today_price(), DayPrice.UNKNOWN)


class TempoDayBoundaryTestCase(unittest.TestCase):
    """A Tempo day runs 06:00 -> 06:00, not midnight to midnight."""

    def setUp(self):
        self.provider = TempoProvider()
        self.provider._today_price = DayPrice.HIGH
        self.provider._tomorrow_price = DayPrice.LOW
        self.provider._today_status = DayStatus.OK
        self.provider._tomorrow_status = DayStatus.OK
        self.provider._last_success = datetime.now()

    def test_upcoming_day_before_6am_is_api_today(self):
        """At 03:00 the red day about to start at 06:00 is the API's today."""
        now = datetime(2026, 1, 6, 3, 0)
        self.assertEqual(self.provider.get_price_for_upcoming_tempo_day(now), DayPrice.HIGH)

    def test_upcoming_day_after_6am_is_api_tomorrow(self):
        now = datetime(2026, 1, 6, 23, 0)
        self.assertEqual(self.provider.get_price_for_upcoming_tempo_day(now), DayPrice.LOW)

    def test_upcoming_day_at_6am_sharp_is_api_tomorrow(self):
        now = datetime(2026, 1, 6, 6, 0)
        self.assertEqual(self.provider.get_price_for_upcoming_tempo_day(now), DayPrice.LOW)

    def test_current_day_before_6am_is_unknown(self):
        """Before 06:00 the day being billed started yesterday, which we never fetch."""
        now = datetime(2026, 1, 6, 3, 0)
        self.assertEqual(self.provider.get_price_for_current_tempo_day(now), DayPrice.UNKNOWN)

    def test_current_day_after_6am_is_api_today(self):
        now = datetime(2026, 1, 6, 14, 0)
        self.assertEqual(self.provider.get_price_for_current_tempo_day(now), DayPrice.HIGH)


if __name__ == '__main__':
    unittest.main()
