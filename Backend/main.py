from flask import Flask, jsonify, request
from threading import Timer
import json

from datetime import datetime

from temperature import collect_temperatures
from localsql import log_heatvalue_if_change, log_setpoint, log_dbg_setpoint
from heat import send_heat
import logging
import sys

LOGGER = logging.getLogger(__name__)

app = Flask(__name__)

config: dict = {}

set_comfort_temp: float = 0.0
set_eco_temp: float = 0.0

temperatures_sources = []


def heat(on: bool):
    log_heatvalue_if_change(on)
    send_heat(config=config, enable=on)


def periodic_tasks():
    global temperatures_sources
    temperatures_sources = collect_temperatures(config)
    setpoint_temperature = weights_the_temp_setting()
    log_dbg_setpoint(setpoint_temperature)
    regulate_heating(setpoint_temperature, temperatures_sources)


def is_in_off_peak(current_time_str: str) -> bool:
    current_time = datetime.strptime(current_time_str, '%H:%M').time()
    for period in config['off_peak']:
        start = datetime.strptime(period['start'], '%H:%M').time()
        end = datetime.strptime(period['end'], '%H:%M').time()
        if start < end:
            if start <= current_time <= end:
                return True
        else:  # Over midnight scenario
            if current_time >= start or current_time <= end:
                return True
    return False


def get_current_hour_min() -> str:
    return datetime.now().strftime('%H:%M')


def weights_the_temp_setting() -> float:
    # Here is the cool stuff
    current_time_str: str = get_current_hour_min()

    # Rule 1 : comfort or Eco T° due to electricity price
    if is_in_off_peak(current_time_str):
        setpoint_temperature = set_comfort_temp
    else:
        setpoint_temperature = set_eco_temp

    LOGGER.info(f'Weight_Setpoint : Step01-offpeak : setpoint={setpoint_temperature}')

    # Rule 2 : reduce T° during deep night
    # deep_night_start = datetime.strptime(config['off_peak']['start'], '%H:%M')
    # deep_night_end = datetime.strptime(config['off_peak']['end'], '%H:%M')

    # ToDo

    # Rule 3 : hysteresys to avoid ping/pong
    # ToDo

    # Rule 4 : Use forecast to start heating during afternoon even if home is hot in order to avoid a sharp drop in temperature
    # ToDo

    return setpoint_temperature


def test_inf(list_to_compute, theshold: float) -> bool:
    for value in list_to_compute:
        if value.temp < theshold:
            return True
    return False


def regulate_heating(setpoint_temperature, temperatures):
    enable_heat = False

    # Ensure no room are not
    if test_inf(temperatures, (setpoint_temperature - 1.5)):
        enable_heat = True
        LOGGER.info(f'Force Heating because one of the room is 1.5° below {setpoint_temperature}')
    else:
        average_temperature = sum(measure.temp for measure in temperatures) / len(temperatures)
        if average_temperature < setpoint_temperature:
            LOGGER.info(f'Enable Heating because setpoint is set to {setpoint_temperature} and average T° is {average_temperature}')
            enable_heat = True

    if not enable_heat:
        LOGGER.info(f'Disable Heating because setpoint is set to {setpoint_temperature} and average T° is {average_temperature}')

    heat(enable_heat)


@app.route('/setpoint', methods=['GET'])
def get_setpoint_temperature():
    return jsonify({
        "comfort_temp": set_comfort_temp,
        "eco_temp": set_eco_temp
    })


@app.route('/setpoint', methods=['POST'])
def set_setpoint_temperature() -> str:
    global set_comfort_temp, set_eco_temp
    try:
        set_comfort_temp = float(request.json['comfort_temp'])
        set_eco_temp = float(request.json['eco_temp'])
        # Update config file
        config['set_temperature']['comfort'] = set_comfort_temp
        config['set_temperature']['eco'] = set_eco_temp
        with open('/container/config/config.json', 'w') as f:
            json.dump(config, f, indent=4)
        log_setpoint(comfort_temp=set_comfort_temp, eco_temp=set_eco_temp)
        periodic_tasks()
        return jsonify({"message": "setpoint temperature updated"}), 200
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid setpoint temperature value"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def load_config() -> dict:
    try:
        with open('/container/config/config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        LOGGER.critical(f'Fail to load program config due to : {e}')
        sys.exit(1)


def init_app():
    global config, set_comfort_temp, set_eco_temp
    config = load_config()
    set_comfort_temp = config['set_temperature']['comfort']
    set_eco_temp = config['set_temperature']['eco']
    log_setpoint(comfort_temp=set_comfort_temp, eco_temp=set_eco_temp)


def periodic_timer_handler():
    periodic_tasks()
    Timer(config['app']['pooling_frequency'], periodic_timer_handler).start()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    init_app()
    periodic_timer_handler()  # Start the periodic task
    app.run(host='0.0.0.0', port=80, debug=True)
