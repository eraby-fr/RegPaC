import unittest
from unittest.mock import patch, MagicMock
from Backend.heat import send_heat

class SendCmd_Actuator(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('requests.post')
    def test_send_heat_on(self, mock_post):
        config = {
            'actuator': {'device': 'heater1'},
            'fhem': {'url': 'http://example.com'}
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        res = send_heat(config=config,enable=True)

        self.assertEqual(res, True)
        mock_post.assert_called_once_with(
            'http://example.com',
            params={"cmd": "set heater1 on", "XHR": "1"}
        )

    @patch('requests.post')
    def test_send_heat_off(self, mock_post):
        config = {
            'actuator': {'device': 'heater1'},
            'fhem': {'url': 'http://example.com'}
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        res = send_heat(config=config,enable=False)

        self.assertEqual(res, True)
        mock_post.assert_called_once_with(
            'http://example.com',
            params={"cmd": "set heater1 off", "XHR": "1"}
        )

    @patch('requests.post')
    def test_send_heat_cmd_fail(self, mock_post):
        config = {
            'actuator': {'device': 'heater1'},
            'fhem': {'url': 'http://example.com'}
        }

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        res = send_heat(config=config,enable=False)
        self.assertEqual(res, False)

        mock_post.assert_called_once_with(
            'http://example.com',
            params={"cmd": "set heater1 off", "XHR": "1"}
        )
