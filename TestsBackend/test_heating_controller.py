from datetime import datetime
import unittest
import json
import sys
import os

current_directory = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_directory, "../Backend")
sys.path.insert(0, backend_path)

from unittest.mock import patch, mock_open
from Backend.main import app, init_app
from Backend.temperature import Measure


class HeatingControllerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    @patch('Backend.main.open', new_callable=mock_open)
    @patch('Backend.main.collect_temperatures', return_value=[Measure(20.0, "1", datetime.now()), Measure(18.2, "2", datetime.now()), Measure(20.7, "3", datetime.now()), Measure(21.1, "4", datetime.now())])  # Avg = 20°
    @patch('Backend.main.load_config', return_value={"set_temperature": {"comfort": 22.0, "eco": 18.0}, "off_peak": [{"start": "00:30", "end": "07:30"}, {"start": "12:30", "end": "14:00"}, {"start": "23:00", "end": "00:10"}]})
    @patch('Backend.main.json.dump')
    @patch('Backend.main.heat')
    @patch('Backend.main.log_setpoint')
    @patch('Backend.main.log_dbg_setpoint')
    def run_generic_test_set_temperature(self, mock_dbg, mock_set, mock_heat, mock_json_dump, mock_config_load, mock_collect_temperatures, mock_open, temp_eco: float, temp_comfort: float, expected_heating_result: bool):
        init_app()
        response = self.app.post('/setpoint', data=json.dumps({'eco_temp': temp_eco, 'comfort_temp': temp_comfort}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        mock_heat.assert_called_once_with(expected_heating_result)

    @patch('Backend.main.get_current_hour_min', return_value="13:30")
    def test_settemp_comfort_heat_on(self, mock_get_current_hour_min):
        self.run_generic_test_set_temperature(temp_eco=19.0, temp_comfort=21.0, expected_heating_result=True)

    @patch('Backend.main.get_current_hour_min', return_value="13:30")
    def test_settemp_comfort_heat_off(self, mock_get_current_hour_min):
        self.run_generic_test_set_temperature(temp_eco=18.0, temp_comfort=19.0, expected_heating_result=False)

    @patch('Backend.main.get_current_hour_min', return_value="00:15")
    def test_settemp_eco_heat_on(self, mock_get_current_hour_min):
        self.run_generic_test_set_temperature(temp_eco=20.5, temp_comfort=21.0, expected_heating_result=True)

    @patch('Backend.main.get_current_hour_min', return_value="00:15")
    def test_settemp_eco_heat_off(self, mock_get_current_hour_min):
        self.run_generic_test_set_temperature(temp_eco=18.0, temp_comfort=22.0, expected_heating_result=False)

    @patch('Backend.main.get_current_hour_min', return_value="00:05")  # OffPeak expected true
    def test_settemp_offpeak_overlap_midnight(self, mock_get_current_hour_min):
        self.run_generic_test_set_temperature(temp_eco=18.0, temp_comfort=22.0, expected_heating_result=True)

    @patch('Backend.main.open', new_callable=mock_open)
    @patch('Backend.main.collect_temperatures', return_value=[Measure(50.0, "1", datetime.now()), Measure(18.4, "2", datetime.now()), Measure(60.7, "3", datetime.now()), Measure(87.1, "4", datetime.now())])  # Avg = 54.05°
    @patch('Backend.main.load_config', return_value={"set_temperature": {"comfort": 22.0, "eco": 18.0}, "off_peak": [{"start": "00:30", "end": "07:30"}, {"start": "12:30", "end": "14:00"}, {"start": "23:00", "end": "00:10"}]})
    @patch('Backend.main.json.dump')
    @patch('Backend.main.heat')
    @patch('Backend.main.get_current_hour_min', return_value="13:30")
    @patch('Backend.main.log_setpoint')
    @patch('Backend.main.log_dbg_setpoint')
    def test_heat_on_if_one_room_below(self, mock_dbg, mock_set, mock_get_current_hour_min, mock_heat, mock_json_dump, mock_config_load, mock_collect_temperatures, mock_open):
        init_app()
        temp_eco = 19.0
        temp_comfort = 20.0
        response = self.app.post('/setpoint', data=json.dumps({'eco_temp': temp_eco, 'comfort_temp': temp_comfort}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        mock_heat.assert_called_once_with(True)


if __name__ == '__main__':
    unittest.main()
