import unittest
from unittest.mock import patch, MagicMock
from heating_controller import app, regulate_heating, collect_temperatures, log_temperatures, sync_temp_db_to_nas, is_in_heures_creuses
import json
from datetime import datetime

class HeatingControllerTestCase(unittest.TestCase):

    @patch('heating_controller.heat')
    @patch('heating_controller.datetime')
    def test_regulate_heating_confort(self, mock_datetime, mock_heat):
        # Simuler l'heure actuelle pour être dans une plage des heures creuses
        mock_datetime.now.return_value = datetime.strptime('23:00', '%H:%M')

        with patch('heating_controller.heures_creuses', [
            {'debut': '22:00', 'fin': '06:00'},
            {'debut': '14:00', 'fin': '16:00'}
        ]):
            with patch('heating_controller.temperatures_sources', {
                "source1": 20.0,
                "source2": 21.0,
                "source3": 19.0
            }):
                regulate_heating()
                mock_heat.assert_called_once_with(True)

    @patch('heating_controller.heat')
    @patch('heating_controller.datetime')
    def test_regulate_heating_eco(self, mock_datetime, mock_heat):
        # Simuler l'heure actuelle pour ne pas être dans une plage des heures creuses
        mock_datetime.now.return_value = datetime.strptime('12:00', '%H:%M')

        with patch('heating_controller.heures_creuses', [
            {'debut': '22:00', 'fin': '06:00'},
            {'debut': '14:00', 'fin': '16:00'}
        ]):
            with patch('heating_controller.temperatures_sources', {
                "source1": 20.0,
                "source2": 21.0,
                "source3": 19.0
            }):
                regulate_heating()
                mock_heat.assert_called_once_with(False)

    def test_is_in_heures_creuses(self):
        self.assertTrue(is_in_heures_creuses('23:00'))
        self.assertTrue(is_in_heures_creuses('05:59'))
        self.assertFalse(is_in_heures_creuses('12:00'))
        self.assertTrue(is_in_heures_creuses('15:00'))

    @patch('heating_controller.sqlite3.connect')
    def test_log_temperatures_with_nas(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        log_temperatures()
        mock_connect.assert_called_once_with('/mnt/NAS/temperature_log.db')
        self.assertTrue(mock_conn.cursor().execute.called)

    @patch('heating_controller.sqlite3.connect')
    @patch('heating_controller.os.path.exists')
    def test_log_temperatures_without_nas(self, mock_exists, mock_connect):
        mock_exists.side_effect = lambda x: x != '/mnt/NAS/temperature_log.db'
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        log_temperatures()
        mock_connect.assert_called_once_with('/tmp/temperature_log.db')
        self.assertTrue(mock_conn.cursor().execute.called)

    @patch('heating_controller.sqlite3.connect')
    @patch('heating_controller.os.path.exists')
    def test_sync_temp_db_to_nas(self, mock_exists, mock_connect):
        mock_exists.side_effect = lambda x: True
        mock_nas_conn = MagicMock()
        mock_temp_conn = MagicMock()
        mock_connect.side_effect = [mock_nas_conn, mock_temp_conn]

        sync_temp_db_to_nas()
        mock_connect.assert_any_call('/mnt/NAS/temperature_log.db')
        mock_connect.assert_any_call('/tmp/temperature_log.db')
        self.assertTrue(mock_nas_conn.cursor().executemany.called)
        self.assertTrue(mock_temp_conn.cursor().execute.called)

    def test_get_temperature(self):
        tester = app.test_client(self)
        response = tester.get('/temperature/source1')
        self.assertEqual(response.status_code, 200)

    def test_set_temperature(self):
        tester = app.test_client(self)
        response = tester.post('/temperature/source1', json={'temperature': 23.0})
        self.assertEqual(response.status_code, 200)

    def test_get_consigne_temperature(self):
        tester = app.test_client(self)
        response = tester.get('/consigne')
        self.assertEqual(response.status_code, 200)

    def test_set_consigne_temperature(self):
        tester = app.test_client(self)
        response = tester.post('/consigne', json={'confort': 21.0, 'eco': 17.0})
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
