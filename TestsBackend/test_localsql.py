import unittest
from unittest.mock import mock_open, patch
from Backend.localsql import log_heatvalue_if_change, log_setpoint, reset_previous_state

class TestLogHeatValue(unittest.TestCase):
    def setUp(self):
        reset_previous_state()  # Reset state before each test

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_initial_log_on(self, mock_makedirs, mock_file):
        log_heatvalue_if_change(True)
        mock_file().write.assert_called_once()
        self.assertIn("100", mock_file().write.call_args[0][0])
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_initial_log_off(self, mock_makedirs, mock_file):
        log_heatvalue_if_change(False)
        mock_file().write.assert_called_once()
        self.assertIn(" 0", mock_file().write.call_args[0][0])
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_no_duplicate_logs(self, mock_makedirs, mock_file):
        log_heatvalue_if_change(True)
        log_heatvalue_if_change(True)
        mock_file().write.assert_called_once()  # Should only log once
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_log_state_change(self, mock_makedirs, mock_file):
        log_heatvalue_if_change(True)
        log_heatvalue_if_change(False)
        log_heatvalue_if_change(True)
        self.assertEqual(mock_file().write.call_count, 3)
        self.assertIn("100", mock_file().write.call_args_list[0][0][0])
        self.assertIn(" 0", mock_file().write.call_args_list[1][0][0])
        self.assertIn("100", mock_file().write.call_args_list[2][0][0])

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_log_setpoint(self, mock_makedirs, mock_file):
        log_setpoint(21.5, 18.0)
        log_setpoint(21.0, 18.0)
        log_setpoint(21.0, 18.0)
        log_setpoint(22.0, 19.2)

        self.assertEqual(mock_file().write.call_count, 4)

        log_entry = mock_file().write.call_args_list[0][0][0]
        self.assertIn("setpoint_comfort 21.5", log_entry)
        self.assertIn("setpoint_eco 18.0", log_entry)

        log_entry = mock_file().write.call_args_list[1][0][0]
        self.assertIn("setpoint_comfort 21.0", log_entry)
        self.assertIn("setpoint_eco 18.0", log_entry)

        log_entry = mock_file().write.call_args_list[2][0][0]
        self.assertIn("setpoint_comfort 21.0", log_entry)
        self.assertIn("setpoint_eco 18.0", log_entry)
        
        log_entry = mock_file().write.call_args_list[3][0][0]
        self.assertIn("setpoint_comfort 22.0", log_entry)
        self.assertIn("setpoint_eco 19.2", log_entry)
if __name__ == "__main__":
    unittest.main()
