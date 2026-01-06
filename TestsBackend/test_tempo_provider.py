import unittest
import sys
import os
from unittest.mock import patch, MagicMock

current_directory = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_directory, "../Backend")
sys.path.insert(0, backend_path)

from Backend.tempo_provider import TempoProvider, DayPrice


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


if __name__ == '__main__':
    unittest.main()
