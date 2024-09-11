import unittest
import json
from unittest.mock import patch, mock_open
from Backend.main import app, init_app

class HeatingControllerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        #self.app.testing = True

    @patch('Backend.main.retrieve_logged_temperature', return_value={'1': 21.0, '2': 22.8, '3': 19.5})
    def test_get_temperature(self, mock_retrieve_logged_temperature):
        response = self.app.get('/temperature/2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, '{"2":22.8}\n')        

    def test_get_temperature_failnodb(self):
        response = self.app.get('/temperature/2')
        self.assertEqual(response.status_code, 500)   
        self.assertIn("database not found", response.text)

    @patch('Backend.main.retrieve_logged_temperature', return_value={'1': 21.0, '2': 22.8, '3': 19.5})
    def test_get_temperature_failwrongsource(self, mock_retrieve_logged_temperature):
        response = self.app.get('/temperature/45')
        self.assertEqual(response.status_code, 404)

    @patch('Backend.main.open', new_callable=mock_open)
    @patch('Backend.main.collect_temperatures', return_value={'1': 18.2, '2': 20.7, '3': 21.1}) #Avg = 20°
    @patch('Backend.main.load_config', return_value={"set_temperature":{"comfort":22.0,"eco":18.0},"off_peak":[{"start":"00:30","end":"07:30"},{"start":"12:30","end":"14:00"}, {"start": "23:00", "end": "00:10"}]})
    @patch('Backend.main.json.dump')
    @patch('Backend.main.heat')
    @patch('Backend.localsql.sqlite3.connect') #to avoid db created on /tmp
    def run_generic_test_set_temperature(self, mock_sql, mock_heat, mock_json_dump, mock_config_load, mock_collect_temperatures, mock_open, temp_eco:float, temp_comfort:float, expected_heating_result:bool):
        init_app()
        response = self.app.post('/setpoint', data=json.dumps({'eco': temp_eco,'comfort': temp_comfort}), content_type='application/json')
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

    @patch('Backend.main.get_current_hour_min', return_value="00:05") #OffPeak expected true
    def test_settemp_offpeak_overlap_midnight(self, mock_get_current_hour_min):
        self.run_generic_test_set_temperature(temp_eco=18.0, temp_comfort=22.0, expected_heating_result=True)

if __name__ == '__main__':
    unittest.main()
