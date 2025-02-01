from flask import Flask, jsonify, request
from threading import Timer
import json

from datetime import datetime

from temperature import collect_temperatures
from localsql import log_heatvalue_if_change, log_temperatures, retrieve_logged_temperature, retrieve_last_logged_temperature

app = Flask(__name__)

config: dict = {}

set_comfort_temp: float = 0.0
set_eco_temp: float = 0.0

temperatures_sources = []

def heat(on: bool):
    log_heatvalue_if_change(on)
    if on:
        print("Heating is ON... Let's plug EnoCean on that")
    else:
        print("Heating is OFF... Let's plug EnoCean on that")

def periodic_tasks():
    global temperatures_sources
    temperatures_sources = collect_temperatures(config)
    setpoint_temperature = weights_the_temp_setting()
    #log_temperatures(temperatures_sources) #ToDo : add the log of the consign temperature
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

def weights_the_temp_setting()-> float:
    #Here is the cool stuff
    current_time_str: str = get_current_hour_min()

    #Rule 1 : comfort or Eco T° due to electricity price
    if is_in_off_peak(current_time_str):
        setpoint_temperature = set_comfort_temp
    else:
        setpoint_temperature = set_eco_temp

    #Rule 2 : reduce T° during deep night 
    #deep_night_start = datetime.strptime(config['off_peak']['start'], '%H:%M')
    #deep_night_end = datetime.strptime(config['off_peak']['end'], '%H:%M')
    
    #ToDo

    #Rule 3 : hysteresys to avoid ping/pong
    #ToDo

    #Rule 4 : Use forecast to start heating during afternoon even if home is hot in order to avoid a sharp drop in temperature
    #ToDo

    return setpoint_temperature

def regulate_heating(setpoint_temperature, temperatures):
    average_temperature = sum(measure.temp for measure in temperatures) / len(temperatures)
    if average_temperature < setpoint_temperature:
        print("Enable Heating because setpoint is set to %.2f and average T° is %.2f" % (setpoint_temperature, average_temperature))
        heat(True)
    else:
        print("Disable Heating because setpoint is set to %.2f and average T° is %.2f" % (setpoint_temperature, average_temperature))
        heat(False)

@app.route('/temperature/<source>', methods=['GET'])
def get_temperature(source):
    item = next((measure for measure in temperatures_sources if measure.name == source), None)
    if item:
        return jsonify({source:item.temp})
    else:
        #ToDo try to retrieve in DB
        return jsonify({"error": "Source not found"}), 404

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
        set_comfort_temp = float(request.json['comfort'])
        set_eco_temp = float(request.json['eco'])
        # Update config file
        config['set_temperature']['comfort'] = set_comfort_temp
        config['set_temperature']['eco'] = set_eco_temp
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        periodic_tasks()
        return jsonify({"message": "setpoint temperature updated"}), 200
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid setpoint temperature value"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/temperature_log', methods=['GET'])
def get_temperature_log():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"error": "Please provide both start_date and end_date"}), 400

    return retrieve_logged_temperature(start_date, end_date)

def load_config() -> dict:
    with open('/container/config/config.json', 'r') as f:
        return json.load(f)
    
def init_app():
    global config, set_comfort_temp, set_eco_temp
    config = load_config()
    set_comfort_temp = config['set_temperature']['comfort']
    set_eco_temp = config['set_temperature']['eco']

def periodic_timer_handler():
    periodic_tasks()
    Timer(config['app']['pooling_frequency'], periodic_timer_handler).start()

if __name__ == '__main__':
    init_app()
    periodic_timer_handler()  # Start the periodic task
    app.run(host='0.0.0.0', port=80, debug=True)
