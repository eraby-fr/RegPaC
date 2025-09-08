import unittest
import Backend.heat
from unittest.mock import patch, MagicMock


class SendCmd_Actuator(unittest.TestCase):
    def setUp(self):
        Backend.heat.timestamp_on_last_sent = 0.0
        Backend.heat.status_on_last_sent = None

    def tearDown(self):
        pass

    @patch('Backend.heat.requests.post')
    def test_send_heat_on(self, mock_post):
        config = {
            'actuator': {'device': 'heater1'},
            'fhem': {'url': 'http://example.com'}
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        res = Backend.heat.send_heat(config=config, enable=True)

        self.assertTrue(res)
        mock_post.assert_called_once_with(
            'http://example.com',
            params={"cmd": "set heater1 on", "XHR": "1"}
        )

    @patch('Backend.heat.requests.post')
    def test_send_heat_off(self, mock_post):
        config = {
            'actuator': {'device': 'heater1'},
            'fhem': {'url': 'http://example.com'}
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        res = Backend.heat.send_heat(config=config, enable=False)

        self.assertTrue(res)
        mock_post.assert_called_once_with(
            'http://example.com',
            params={"cmd": "set heater1 off", "XHR": "1"}
        )

    @patch('Backend.heat.requests.post')
    def test_send_heat_cmd_fail(self, mock_post):
        config = {
            'actuator': {'device': 'heater1'},
            'fhem': {'url': 'http://example.com'}
        }

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        res = Backend.heat.send_heat(config=config, enable=False)
        self.assertFalse(res)

        mock_post.assert_called_once_with(
            'http://example.com',
            params={"cmd": "set heater1 off", "XHR": "1"}
        )

    @patch('Backend.heat.requests.post')
    @patch('Backend.heat.time.time')
    def test_send_heat_with_time_gap(self, mock_time, mock_post):
        config = {
            'actuator': {'device': 'heater1'},
            'fhem': {'url': 'http://example.com'}
        }

        # Time simulation :
        # - 1st Call→ t=10000
        # - 2nd Call → t=10300 (gap < ellapsed_time_before_force_sent)
        # - 3nd Call → t=15000 (gap > ellapsed_time_before_force_sent)
        mock_time.side_effect = [10000.0, 10300.0, 15000.0]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # 1st call (t=10000)
        res1 = Backend.heat.send_heat(config=config, enable=True)
        self.assertTrue(res1)

        # 2nd call (t=10300)
        res2 = Backend.heat.send_heat(config=config, enable=True)
        self.assertTrue(res2)

        # 3nd call (t=15000)
        res3 = Backend.heat.send_heat(config=config, enable=True)
        self.assertTrue(res3)

        self.assertEqual(mock_post.call_count, 2)
        mock_post.assert_any_call(
            'http://example.com',
            params={"cmd": "set heater1 on", "XHR": "1"}
        )
        mock_post.assert_any_call(
            'http://example.com',
            params={"cmd": "set heater1 on", "XHR": "1"}
        )

    @patch('Backend.heat.requests.post')
    @patch('Backend.heat.time.time')
    def test_send_heat_with_time_gap_and_change(self, mock_time, mock_post):
        config = {
            'actuator': {'device': 'heater1'},
            'fhem': {'url': 'http://example.com'}
        }

        # Time simulation :
        # - 1st Call→ t=10000
        # - 2nd Call → t=10300 (gap < ellapsed_time_before_force_sent) but change
        # - 3nd Call → t=10600 (gap < ellapsed_time_before_force_sent) but change
        mock_time.side_effect = [10000.0, 10300.0, 10600.0]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # 1st call (t=10000)
        res1 = Backend.heat.send_heat(config=config, enable=True)
        self.assertTrue(res1)

        # 2nd call (t=10300)
        res2 = Backend.heat.send_heat(config=config, enable=False)
        self.assertTrue(res2)

        # 3nd call (t=10600)
        res3 = Backend.heat.send_heat(config=config, enable=True)
        self.assertTrue(res3)

        self.assertEqual(mock_post.call_count, 3)
        mock_post.assert_any_call(
            'http://example.com',
            params={"cmd": "set heater1 on", "XHR": "1"}
        )
        mock_post.assert_any_call(
            'http://example.com',
            params={"cmd": "set heater1 off", "XHR": "1"}
        )
        mock_post.assert_any_call(
            'http://example.com',
            params={"cmd": "set heater1 on", "XHR": "1"}
        )

    @patch('Backend.heat.requests.post')
    @patch('Backend.heat.time.time')
    def test_cornercase_send_heat_with_time_gap_and_change_and_fail(self, mock_time, mock_post):
        config = {
            'actuator': {'device': 'heater1'},
            'fhem': {'url': 'http://example.com'}
        }

        # Time simulation :
        # - 1st Call→ t=10000 + 1entry because there is an hiden call to time() in error case
        # - 2nd Call → t=10300 (gap < ellapsed_time_before_force_sent) but change
        # - 3nd Call → t=10600 (gap < ellapsed_time_before_force_sent) but change
        mock_time.side_effect = [10000.0, 10000.0, 10300.0, 10600.0]

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Internal Error"

        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.text = "OK"

        mock_post.side_effect = [mock_response_fail, mock_response_ok, mock_response_ok]

        print("mock_time call count before:", mock_time.call_count)
        # 1st call (t=10000)
        res1 = Backend.heat.send_heat(config=config, enable=False)
        self.assertFalse(res1)

        # 2nd call (t=10300)
        res2 = Backend.heat.send_heat(config=config, enable=False)
        self.assertTrue(res2)

        # 3nd call (t=10600)
        res3 = Backend.heat.send_heat(config=config, enable=False)
        self.assertTrue(res3)

        self.assertEqual(mock_post.call_count, 2)
        mock_post.assert_any_call(
            'http://example.com',
            params={"cmd": "set heater1 off", "XHR": "1"}
        )
        mock_post.assert_any_call(
            'http://example.com',
            params={"cmd": "set heater1 off", "XHR": "1"}
        )
