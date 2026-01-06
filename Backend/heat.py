import requests
import logging
import time

LOGGER = logging.getLogger(__name__)

ellapsed_time_before_force_sent: float = 3600.0
timestamp_on_last_sent: float = 0.0
status_on_last_sent: bool = None


def send_heat(config: dict, enable: bool):
    global timestamp_on_last_sent
    global status_on_last_sent
    now = time.time()
    if status_on_last_sent != enable or (now - timestamp_on_last_sent) > ellapsed_time_before_force_sent:
        timestamp_on_last_sent = now

        device = config['actuator']['device']
        if enable:
            params = {
                "cmd": f"set {device} on",
                "XHR": "1"
            }
        else:
            params = {
                "cmd": f"set {device} off",
                "XHR": "1"
            }

        try:
            response = requests.post(config['fhem']['url'], params=params)
            if response.status_code == 200:
                status_on_last_sent = enable
                LOGGER.info(f"Success to switch heat to {enable}")
                return True
            else:
                LOGGER.warning(f"Request to switch heat to {enable} failed with status code {response.status_code}: {response.text}")
                return False
        except requests.RequestException as e:
            LOGGER.warning(f"Request to switch heat to {enable} failed with exception : {e}")
            return False
    else:
        return True

def get_heat_status() -> bool:
    return status_on_last_sent