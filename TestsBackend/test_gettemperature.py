import unittest
import datetime
from unittest.mock import patch, MagicMock
from Backend.temperature import collect_temperatures


class SendCmd_Sensors(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('requests.post')
    def test_gettemp_server_emptyanswer(self, mock_post):
        config = {
            'sensors': [
                {
                    'name': 'Room Alice',
                    'device': 'EnO_12345678'
                },
                {
                    'name': 'Room Bob',
                    'device': 'EnO_854321'
                }
            ],
            'fhem': {'url': 'http://example.com'}
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        measures = collect_temperatures(config=config)
        self.assertEqual(len(measures), 0)

    @patch('requests.post')
    def test_gettemp_server_400answer(self, mock_post):
        config = {
            'sensors': [
                {
                    'name': 'Room Alice',
                    'device': 'EnO_12345678'
                },
                {
                    'name': 'Room Bob',
                    'device': 'EnO_854321'
                }
            ],
            'fhem': {'url': 'http://example.com'}
        }

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        measures = collect_temperatures(config=config)
        self.assertEqual(len(measures), 0)

    @patch('requests.post')
    def test_gettemp_server_ok_1fullres(self, mock_post):
        config = {
            'sensors': [
                {
                    'name': 'Room Alice',
                    'device': 'EnO_12345678'
                }
            ],
            'fhem': {'url': 'http://example.com'}
        }

        response = {
            'Arg': 'EnO_12345678',
            'Results': [{
                'Name': 'EnO_12345678',
                'PossibleSets': '',
                'PossibleAttrs': 'blahblahblah',
                'Internals': {
                    'DEF': '01959B1C',
                    'FUUID': '66f16a6a-f33f-3e5d-cb3d-e1ad4a6c433c328b',
                    'IODev': 'TCM_ESP3_0',
                    'LASTInputDev': 'TCM_ESP3_0',
                    'MSGCNT': '415',
                    'NAME': 'EnO_12345678',
                    'NR': '54',
                    'NTFY_ORDER': '50-EnO_12345678',
                    'STATE': '19.5',
                    'TCM_ESP3_0_DestinationID': 'FFFFFFFF',
                    'TCM_ESP3_0_MSGCNT': '415',
                    'TCM_ESP3_0_PacketType': '1',
                    'TCM_ESP3_0_RSSI': '-68',
                    'TCM_ESP3_0_ReceivingQuality': 'excellent',
                    'TCM_ESP3_0_RepeatingCounter': '0',
                    'TCM_ESP3_0_SubTelNum': '3',
                    'TCM_ESP3_0_TIME': '2024-12-10 23:53:39',
                    'TYPE': 'EnOcean',
                    'eventCount': '415'
                },
                'Readings': {
                    'IODev': {'Value': 'TCM_ESP3_0', 'Time': '2024-12-05 13:53:11'},
                    'state': {'Value': '19.5', 'Time': '2024-12-10 23:53:39'},
                    'teach': {'Value': '4BS teach-in accepted EEP A5-02-05 Manufacturer: EnOcean GmbH'},
                    'temperature': {'Value': '15.76', 'Time': '2024-01-30 11:45:20'}
                },
                'Attributes': {
                    'IODev': 'TCM_ESP3_0',
                    'alias': 'mY rOOM',
                    'creator': 'autocreate',
                    'eep': 'A5-02-05',
                    'manufID': '00B',
                    'room': 'EnOcean',
                    'subType': 'tempSensor.05',
                    'teachMethod': '4BS'
                }
            }],
            'totalResultsReturned': 1
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response
        mock_post.return_value = mock_response

        measures = collect_temperatures(config=config)
        self.assertEqual(len(measures), 1)
        self.assertEqual(measures[0].temp, float(15.76))
        self.assertEqual(measures[0].name, "Room Alice")
        self.assertEqual(measures[0].timestamp, datetime.datetime(year=2024, month=1, day=30, hour=11, minute=45, second=20))

    @patch('requests.post')
    def test_gettemp_server_ok_1device2responses(self, mock_post):
        config = {
            'sensors': [
                {
                    'name': 'Room Alice',
                    'device': 'EnO_12345678'
                }
            ],
            'fhem': {'url': 'http://example.com'}
        }

        response = {
            'Arg': 'EnO_12345678',
            'Results': [{
                'Readings': {
                    'temperature': {'Value': '19.5', 'Time': '2024-12-10 23:53:39'}
                },
            }, {
                'Readings': {
                    'temperature': {'Value': '20', 'Time': '2024-12-10 20:00:30'}
                },
            }],
            'totalResultsReturned': 1
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response
        mock_post.return_value = mock_response

        measures = collect_temperatures(config=config)
        self.assertEqual(len(measures), 1)
        self.assertEqual(measures[0].temp, float(19.5))
        self.assertEqual(measures[0].name, "Room Alice")
        self.assertEqual(measures[0].timestamp, datetime.datetime(year=2024, month=12, day=10, hour=23, minute=53, second=39))
