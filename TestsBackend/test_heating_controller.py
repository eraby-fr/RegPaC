from datetime import datetime
import unittest
import json
import sys
import os

current_directory = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_directory, "../Backend")
sys.path.insert(0, backend_path)

from unittest.mock import patch, mock_open
import Backend.main as main
from Backend.main import app, init_app
from Backend.temperature import Measure

# main.py imports its siblings as `from tempo_provider import ...` (Backend/ is on
# sys.path above), so `tempo_provider` and `Backend.tempo_provider` are two distinct
# module objects carrying two distinct DayPrice enums, whose members never compare
# equal. Use the one main.py actually compares against, or every Tempo assertion
# silently passes for the wrong reason.
import tempo_provider as backend_tempo_provider

DayPrice = backend_tempo_provider.DayPrice
DayStatus = backend_tempo_provider.DayStatus


def force_tempo_prices(today_price: DayPrice, tomorrow_price: DayPrice):
    """Pin the colours held by the provider main.py actually uses.

    Patching Backend.tempo_provider.TempoProvider has no effect here : main.py
    does `from tempo_provider import TempoProvider`, so the name is already
    bound. Seeding the real provider also keeps the Tempo-day (06:00 -> 06:00)
    logic under test instead of mocking it away.
    """
    provider = main.tempo_provider
    provider._today_price = today_price
    provider._tomorrow_price = tomorrow_price
    provider._today_status = DayStatus.OK
    provider._tomorrow_status = DayStatus.OK
    provider._last_success = datetime.now()


class HeatingControllerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    @patch('Backend.main.open', new_callable=mock_open)
    @patch('Backend.main.collect_temperatures', return_value=[Measure(20.0, "1", datetime.now()), Measure(18.2, "2", datetime.now()), Measure(20.7, "3", datetime.now()), Measure(21.1, "4", datetime.now())])  # Avg = 20°
    @patch('Backend.main.load_config', return_value={"set_temperature": {"off_peak_cost": 22.0, "full_cost": 18.0}, "off_peak": [{"start": "00:30", "end": "07:30"}, {"start": "12:30", "end": "14:00"}, {"start": "23:00", "end": "00:10"}], "tempo": {"temperature_reduction_high_cost": -2.0, "temperature_increase_prior_to_high_cost": 2.0}, "app": {"pooling_frequency": 60, "pooling_provider_frequency": 10800}})
    @patch('Backend.main.json.dump')
    @patch('Backend.main.heat')
    @patch('Backend.main.log_setpoint')
    @patch('Backend.main.log_dbg_setpoint')
    def run_generic_test_set_temperature(self, mock_dbg, mock_set, mock_heat, mock_json_dump, mock_config_load, mock_collect_temperatures, mock_open, temp_full_cost: float, temp_off_peak: float, expected_heating_result: bool, today_price=DayPrice.NORMAL, tomorrow_price=DayPrice.NORMAL):
        init_app()
        force_tempo_prices(today_price, tomorrow_price)
        response = self.app.post('/setpoint', data=json.dumps({'off_peak_cost': temp_off_peak, 'full_cost': temp_full_cost}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        mock_heat.assert_called_once_with(expected_heating_result)

    @patch('Backend.main.get_current_hour_min', return_value="13:30")
    def test_settemp_comfort_heat_on(self, mock_get_current_hour_min):
        self.run_generic_test_set_temperature(temp_full_cost=19.0, temp_off_peak=21.0, expected_heating_result=True)

    @patch('Backend.main.get_current_hour_min', return_value="13:30")
    def test_settemp_comfort_heat_off(self, mock_get_current_hour_min):
        self.run_generic_test_set_temperature(temp_full_cost=18.0, temp_off_peak=19.0, expected_heating_result=False)

    @patch('Backend.main.get_current_hour_min', return_value="00:15")
    def test_settemp_eco_heat_on(self, mock_get_current_hour_min):
        self.run_generic_test_set_temperature(temp_full_cost=20.5, temp_off_peak=21.0, expected_heating_result=True)

    @patch('Backend.main.get_current_hour_min', return_value="00:15")
    def test_settemp_eco_heat_off(self, mock_get_current_hour_min):
        self.run_generic_test_set_temperature(temp_full_cost=18.0, temp_off_peak=22.0, expected_heating_result=False)

    @patch('Backend.main.get_current_hour_min', return_value="00:05")  # OffPeak expected true
    def test_settemp_offpeak_overlap_midnight(self, mock_get_current_hour_min):
        self.run_generic_test_set_temperature(temp_full_cost=18.0, temp_off_peak=22.0, expected_heating_result=True)

    @patch('Backend.main.open', new_callable=mock_open)
    @patch('Backend.main.collect_temperatures', return_value=[Measure(50.0, "1", datetime.now()), Measure(18.4, "2", datetime.now()), Measure(60.7, "3", datetime.now()), Measure(87.1, "4", datetime.now())])  # Avg = 54.05°
    @patch('Backend.main.load_config', return_value={"set_temperature": {"off_peak_cost": 22.0, "full_cost": 18.0}, "off_peak": [{"start": "00:30", "end": "07:30"}, {"start": "12:30", "end": "14:00"}, {"start": "23:00", "end": "00:10"}], "tempo": {"temperature_reduction_high_cost": -2.0, "temperature_increase_prior_to_high_cost": 2.0}, "app": {"pooling_frequency": 60, "pooling_provider_frequency": 10800}})
    @patch('Backend.main.json.dump')
    @patch('Backend.main.heat')
    @patch('Backend.main.get_current_hour_min', return_value="13:30")
    @patch('Backend.main.log_setpoint')
    @patch('Backend.main.log_dbg_setpoint')
    def test_heat_on_if_one_room_below(self, mock_dbg, mock_set, mock_get_current_hour_min, mock_heat, mock_json_dump, mock_config_load, mock_collect_temperatures, mock_open):
        init_app()
        force_tempo_prices(DayPrice.NORMAL, DayPrice.NORMAL)
        temp_full_cost = 19.0
        temp_off_peak = 20.0
        response = self.app.post('/setpoint', data=json.dumps({'off_peak_cost': temp_off_peak, 'full_cost': temp_full_cost}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        mock_heat.assert_called_once_with(True)


def prod_like_config():
    """Off-peak windows as deployed : one of them sits before 06:00."""
    return {
        "set_temperature": {"off_peak_cost": 19.5, "full_cost": 19.0},
        "off_peak": [{"start": "00:00", "end": "06:00"}, {"start": "22:00", "end": "23:59"}],
        "tempo": {"temperature_reduction_high_cost": -2.0, "temperature_increase_prior_to_high_cost": 2.0},
        "app": {"pooling_frequency": 60, "pooling_provider_frequency": 10800}
    }


def night_full_cost_config():
    """Same, but the night is billed at full cost, to exercise rule 2 before 06:00."""
    config = prod_like_config()
    config["off_peak"] = [{"start": "22:00", "end": "23:59"}]
    return config


class TempoDayRulesTestCase(unittest.TestCase):
    """Rules 1 and 2 must follow Tempo days (06:00 -> 06:00), not calendar days."""

    def setUp(self):
        self.app = app.test_client()

    @patch('Backend.main.open', new_callable=mock_open)
    @patch('Backend.main.collect_temperatures', return_value=[Measure(20.0, "Room", datetime.now())])
    @patch('Backend.main.json.dump')
    @patch('Backend.main.heat')
    @patch('Backend.main.log_setpoint')
    @patch('Backend.main.log_dbg_setpoint')
    def compute_setpoint(self, mock_dbg, mock_set, mock_heat, mock_json_dump, mock_collect, mock_open, config_factory, now, today_price, tomorrow_price):
        with patch('Backend.main.load_config', side_effect=config_factory):
            init_app()
        force_tempo_prices(today_price, tomorrow_price)
        with patch('Backend.main.get_now', return_value=now):
            response = self.app.post('/setpoint',
                                     data=json.dumps({'off_peak_cost': 19.5, 'full_cost': 19.0}),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        mock_dbg.assert_called_once()
        return mock_dbg.call_args[0][0]

    def test_preheat_during_the_night_before_a_red_day(self):
        """At 03:00 the red day starting at 06:00 is the API's *today*.

        This is the case the previous code missed : it read 'tomorrow' and never
        pre-heated on an off-peak window placed between midnight and 06:00.
        """
        setpoint = self.compute_setpoint(config_factory=prod_like_config,
                                         now=datetime(2026, 1, 6, 3, 0),
                                         today_price=DayPrice.HIGH,
                                         tomorrow_price=DayPrice.LOW)
        self.assertEqual(setpoint, 21.5)  # 19.5 off-peak + 2.0

    def test_no_preheat_at_night_for_the_day_after_the_upcoming_one(self):
        setpoint = self.compute_setpoint(config_factory=prod_like_config,
                                         now=datetime(2026, 1, 6, 3, 0),
                                         today_price=DayPrice.LOW,
                                         tomorrow_price=DayPrice.HIGH)
        self.assertEqual(setpoint, 19.5)  # untouched off-peak setpoint

    def test_preheat_in_the_evening_before_a_red_day(self):
        """At 23:00 the next Tempo day to start is the API's tomorrow."""
        setpoint = self.compute_setpoint(config_factory=prod_like_config,
                                         now=datetime(2026, 1, 6, 23, 0),
                                         today_price=DayPrice.LOW,
                                         tomorrow_price=DayPrice.HIGH)
        self.assertEqual(setpoint, 21.5)

    def test_reduction_during_a_red_day(self):
        setpoint = self.compute_setpoint(config_factory=prod_like_config,
                                         now=datetime(2026, 1, 6, 14, 0),
                                         today_price=DayPrice.HIGH,
                                         tomorrow_price=DayPrice.LOW)
        self.assertEqual(setpoint, 17.0)  # 19.0 full cost - 2.0

    def test_no_reduction_before_6am_on_a_red_calendar_day(self):
        """Before 06:00 the red tariff has not started yet, so no reduction."""
        setpoint = self.compute_setpoint(config_factory=night_full_cost_config,
                                         now=datetime(2026, 1, 6, 3, 0),
                                         today_price=DayPrice.HIGH,
                                         tomorrow_price=DayPrice.LOW)
        self.assertEqual(setpoint, 19.0)  # untouched full-cost setpoint


if __name__ == '__main__':
    unittest.main()
