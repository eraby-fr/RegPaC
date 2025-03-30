import os
import time

previous_state = None

def log_heatvalue_if_change(on: bool):
    global previous_state
    current_year = time.strftime("%Y")
    log_file = f"/tmp/fhem_logs/heat_{current_year}.log"
    timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
    status = "on" if on else "off"
    log_entry = f"{timestamp} heater {status}\n"
    
    if previous_state != on:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a") as file:
            file.write(log_entry)
        previous_state = on

def log_setpoint(comfort_temp: float, eco_temp: float):
    current_year = time.strftime("%Y")
    log_file = f"/tmp/fhem_logs/setpoint_{current_year}.log"
    timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
    log_entry = f"{timestamp} setpoint_comfort {comfort_temp}, setpoint_eco {eco_temp}\n"
    
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as file:
        file.write(log_entry) 

def reset_previous_state():
    global previous_state
    previous_state = None