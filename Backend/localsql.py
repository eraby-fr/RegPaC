import os
import time

previous_state = None


def log_heatvalue_if_change(on: bool):
    global previous_state
    current_year = time.strftime("%Y")
    log_file = f"/tmp/fhem_logs/regpac_heat-{current_year}.log"
    timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
    status = "100" if on else "0"
    log_entry = f"{timestamp} heater power: {status}\n"

    if previous_state != on:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a") as file:
            file.write(log_entry)
        previous_state = on


def log_setpoint(comfort_temp: float, eco_temp: float):
    current_year = time.strftime("%Y")
    log_file = f"/tmp/fhem_logs/regpac_setpoint-{current_year}.log"
    timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
    log_entry = f"{timestamp} setpoint comfort: {comfort_temp}\n{timestamp} setpoint eco: {eco_temp}\n"

    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as file:
        file.write(log_entry)


def log_dbg_setpoint(value: float):
    current_year = time.strftime("%Y")
    log_file = f"/tmp/fhem_logs/regpac_dbg_setpoint-{current_year}.log"
    timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
    log_entry = f"{timestamp} debug setpoint: {value}\n"

    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as file:
        file.write(log_entry)


def reset_previous_state():
    global previous_state
    previous_state = None
