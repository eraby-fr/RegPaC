import unittest
import os
import datetime
from unittest.mock import patch
from Backend.localsql import log_heatvalue_if_change, retrieve_heat_values, log_temperatures, retrieve_logged_temperature, retrieve_last_logged_temperature
import time

class LocalSQLTestCase(unittest.TestCase):
    _sql_ut_path: str = "/tmp/MUST-BE-DELETED_tests_sql_regpac_log_db.db"
    _sql_ut_ramfile_path: str = "/tmp/MUST-BE-DELETED_ramfile_tests_sql_regpac_log_db.db"

    def setUp(self):
        self.remove_file_if_exists(self._sql_ut_path)
        self.remove_file_if_exists(self._sql_ut_ramfile_path)

    def tearDown(self):
        self.remove_file_if_exists(self._sql_ut_path)
        self.remove_file_if_exists(self._sql_ut_ramfile_path)

    def remove_file_if_exists(self, path:str):
        if os.path.exists(path):
            os.remove(path)

    @patch('Backend.localsql.sqlite3.connect')
    @patch('Backend.localsql.sync_tmp_db_to_nas_db_if_necessary')
    @patch('Backend.localsql.need_to_sync', return_value=False)
    def test_heatvalue_fallback_tmpfolder(self, mock_sync, mock_sync_heat_db_to_nas, mock_connect):
        log_heatvalue_if_change(on=True)
        mock_connect.assert_called_once_with('/tmp/RegPac.db')
        mock_sync_heat_db_to_nas.assert_not_called()

    @patch('Backend.localsql.get_db_path', return_value=_sql_ut_path)
    @patch('Backend.localsql.need_to_sync', return_value=False)
    def test_heating_logging(self, mock_sync, mock_db_path):
        log_heatvalue_if_change(on=True)
        time.sleep(1)
        log_heatvalue_if_change(on=True)
        time.sleep(1)
        log_heatvalue_if_change(on=True)
        time.sleep(1)
        log_heatvalue_if_change(on=False)
        time.sleep(1)
        log_heatvalue_if_change(on=True)
        time.sleep(1)
        log_heatvalue_if_change(on=False)
        time.sleep(1)
        log_heatvalue_if_change(on=False)
        time.sleep(1)

        log_entries = retrieve_heat_values(datetime.datetime.now() - datetime.timedelta(days=1), datetime.datetime.now())
        self.assertEqual(len(log_entries), 4)

        log_heatvalue_if_change(on=False)
        time.sleep(1)
        log_entries = retrieve_heat_values(datetime.datetime.now() - datetime.timedelta(days=1), datetime.datetime.now())
        self.assertEqual(len(log_entries), 4)
        self.assertEqual(log_entries[0]['state'], True)
        self.assertEqual(log_entries[1]['state'], False)
        self.assertEqual(log_entries[2]['state'], True)
        self.assertEqual(log_entries[3]['state'], False)


    @patch('Backend.localsql.get_db_path', return_value=_sql_ut_path)
    @patch('Backend.localsql.need_to_sync', return_value=False)
    def test_temperatures_logging(self, mock_sync, mock_db_path):
        log_temperatures({'1': 1.1, '2': 1.2, '3': 1.3, '4': 1.4})
        time.sleep(1)
        log_temperatures({'1': 2.1, '2': 2.2, '3': 2.3, '4': 2.4})
        time.sleep(1)
        last_inserted_values = {'1': 3.1, '2': 3.2, '3': 3.3, '4': 3.4}
        log_temperatures(last_inserted_values)

        temperature_entries = retrieve_logged_temperature(datetime.datetime.now() - datetime.timedelta(days=1), datetime.datetime.now())
        self.assertEqual(len(temperature_entries), 3)
        self.assertEqual(temperature_entries[2]["source1"], last_inserted_values["1"])
        self.assertEqual(temperature_entries[2]["source2"], last_inserted_values["2"])
        self.assertEqual(temperature_entries[2]["source3"], last_inserted_values["3"])
        self.assertEqual(temperature_entries[2]["source4"], last_inserted_values["4"])

        last_values = retrieve_last_logged_temperature()
        self.assertEqual(last_values, last_inserted_values)

#TODO Control sync
    @patch('Backend.localsql.get_db_path')
    @patch('Backend.localsql.get_remote_file_path', return_value=_sql_ut_path)
    @patch('Backend.localsql.get_local_ramfile_path', return_value=_sql_ut_ramfile_path)
    @patch('Backend.localsql.remote_file_can_be_created', return_value=True)
    def test_sync_tmp2nas(self, mock_filecanbecreated, mock_tmp_path, mock_path, mock_db_path):
        input_temp = {
            1: 20.0, 
            2: 21.5, 
            3: 16.0, 
            4: 17.0, 
            5: 18.0
            }
        expectations_temp = input_temp
        
        input_heat = {
            1: False, 
            2: False, 
            3: True, 
            4: True, 
            5: True
            }
        expectations_heat = {
            1: False, 
            2: False, #Corner case : NAS is not available so tool can't check the previous value.
            3: True
            }

        #Log value in NAS
        mock_db_path.return_value = self._sql_ut_path
        step: int = 1
        log_temperatures({'1': input_temp[step], '2': input_temp[step], '3': input_temp[step], '4': input_temp[step]})
        log_heatvalue_if_change(on=input_heat[step])
        time.sleep(1)

        #Make the NAS unavailable
        mock_db_path.return_value = self._sql_ut_ramfile_path
        step = 2
        log_temperatures({'1': input_temp[step], '2': input_temp[step], '3': input_temp[step], '4': input_temp[step]})
        log_heatvalue_if_change(on=input_heat[step])
        time.sleep(1)

        step=3
        log_temperatures({'1': input_temp[step], '2': input_temp[step], '3': input_temp[step], '4': input_temp[step]})
        log_heatvalue_if_change(on=input_heat[step])
        time.sleep(1)

        step=4
        log_temperatures({'1': input_temp[step], '2': input_temp[step], '3': input_temp[step], '4': input_temp[step]})
        log_heatvalue_if_change(on=input_heat[step])
        time.sleep(1)

        #Make the NAS available
        mock_db_path.stop()

        step=5
        log_temperatures({'1': input_temp[step], '2': input_temp[step], '3': input_temp[step], '4': input_temp[step]})
        log_heatvalue_if_change(on=input_heat[step])
        time.sleep(1)

        #Check if all the values are in NAS in correct order
        temperature_entries = retrieve_logged_temperature(datetime.datetime.now() - datetime.timedelta(days=1), datetime.datetime.now())
        self.assertEqual(len(temperature_entries), len(expectations_temp))
        self.assertEqual(temperature_entries[0]["source1"], expectations_temp[1])
        self.assertEqual(temperature_entries[1]["source1"], expectations_temp[2])
        self.assertEqual(temperature_entries[2]["source1"], expectations_temp[3])
        self.assertEqual(temperature_entries[3]["source1"], expectations_temp[4])
        self.assertEqual(temperature_entries[4]["source1"], expectations_temp[5])

        self.assertEqual(temperature_entries[0]["source2"], expectations_temp[1])
        self.assertEqual(temperature_entries[1]["source2"], expectations_temp[2])
        self.assertEqual(temperature_entries[2]["source2"], expectations_temp[3])
        self.assertEqual(temperature_entries[3]["source2"], expectations_temp[4])
        self.assertEqual(temperature_entries[4]["source2"], expectations_temp[5])

        self.assertEqual(temperature_entries[0]["source3"], expectations_temp[1])
        self.assertEqual(temperature_entries[1]["source3"], expectations_temp[2])
        self.assertEqual(temperature_entries[2]["source3"], expectations_temp[3])
        self.assertEqual(temperature_entries[3]["source3"], expectations_temp[4])
        self.assertEqual(temperature_entries[4]["source3"], expectations_temp[5])

        self.assertEqual(temperature_entries[0]["source4"], expectations_temp[1])
        self.assertEqual(temperature_entries[1]["source4"], expectations_temp[2])
        self.assertEqual(temperature_entries[2]["source4"], expectations_temp[3])
        self.assertEqual(temperature_entries[3]["source4"], expectations_temp[4])
        self.assertEqual(temperature_entries[4]["source4"], expectations_temp[5])

        log_entries = retrieve_heat_values(datetime.datetime.now() - datetime.timedelta(days=1), datetime.datetime.now())
        self.assertEqual(len(log_entries), len(expectations_heat))
        self.assertEqual(log_entries[0]['state'], expectations_heat[1])
        self.assertEqual(log_entries[0]['state'], expectations_heat[2])
        self.assertEqual(log_entries[0]['state'], expectations_heat[3])

if __name__ == '__main__':
    unittest.main()