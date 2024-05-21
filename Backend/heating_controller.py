from flask import Flask, jsonify, request
from threading import Timer
import json

from datetime import datetime

from temperature import collect_temperatures
from localsql import log_heatvalue_if_change, log_temperatures, retrieve_logged_temperature


app = Flask(__name__)

with open('config.json', 'r') as f:
    config = json.load(f)

set_comfort_temp = config['set_temperature']['comfort']
set_eco_temp = config['set_temperature']['eco']

temperatures_sources = {
    "source1": 0.0,
    "source2": 0.0,
    "source3": 0.0
}

def heat(on: bool):

    log_heatvalue_if_change(on)

    if on:
        print("Heating is ON... Let's plug EnoCean on that")
    else:
        print("Heating is OFF... Let's plug EnoCean on that")

def is_in_off_peak(current_time):
    current_time = datetime.strptime(current_time, '%H:%M').time()
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

def weights_the_temp_setting():
    #Here is the cool stuff
    current_time_str = datetime.now().strftime('%H:%M')

    #Rule 1 : comfort or Eco T° due to electricity price
    if is_in_off_peak(current_time_str):
        setpoint_temperature = set_comfort_temp
    else:
        setpoint_temperature = set_eco_temp

    #Rule 2 : reduce T° during deep night 
    #ToDo

    #Rule 3 : hysteresys to avoid ping/pong
    #ToDo

    #Rule 4 : Use forecast to start heating during afternoon even if home is hot in order to avoid a sharp drop in temperature
    #ToDo

    return setpoint_temperature

def regulate_heating(setpoint_temperature, temperatures):
    average_temperature = sum(temperatures.values()) / len(temperatures)
    if average_temperature < setpoint_temperature:
        print("Enable Heating because setpoint is set to %.2f and average T° is %.2f" % (setpoint_temperature, average_temperature))
        heat(True)
    else:
        print("Disable Heating because setpoint is set to %.2f and average T° is %.2f" % (setpoint_temperature, average_temperature))
        heat(False)

def periodic_task():
    temperatures_sources = collect_temperatures()
    setpoint_temperature = weights_the_temp_setting()
    log_temperatures(temperatures_sources) #ToDo : add the log of the consign temperature
    regulate_heating(setpoint_temperature, temperatures_sources)
    Timer(20, periodic_task).start()

@app.route('/temperature/<source>', methods=['GET'])
def get_temperature(source):
    if source in temperatures_sources:
        return jsonify({source: temperatures_sources[source]})
    else:
        return jsonify({"error": "Source not found"}), 404

@app.route('/setpoint', methods=['GET'])
def get_setpoint_temperature():
    return jsonify({
        "comfort_temp": set_comfort_temp,
        "eco_temp": set_eco_temp
    })

@app.route('/setpoint', methods=['POST'])
def set_setpoint_temperature():
    global set_comfort_temp, set_eco_temp
    try:
        set_comfort_temp = float(request.json['comfort'])
        set_eco_temp = float(request.json['eco'])
        # Update config file
        config['set_temperature']['comfort'] = set_comfort_temp
        config['set_temperature']['eco'] = set_eco_temp
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        regulate_heating()
        return jsonify({"message": "setpoint temperature updated"}), 200
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid setpoint temperature value"}), 400

@app.route('/temperature_log', methods=['GET'])
def get_temperature_log():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"error": "Please provide both start_date and end_date"}), 400

    return retrieve_logged_temperature(start_date, end_date)

if __name__ == '__main__':
    periodic_task()  # Start the periodic task
    app.run(debug=True)
