import requests

from datetime import datetime

class Measure:
    def __init__(self, temperature: float, name: str, timestamp: datetime):
        self.temp = temperature
        self.name = name
        self.timestamp = timestamp
    
    def print(self):
        print(f"{self.name} : {self.temperature}°C - collected at {self.timestamp}")
        
def collect_temperatures(config: dict):
    temperatures_sources = []

    for sensor in config['sensors']:
        temp, time = send_request(url=config['fhem']['url'], device=sensor['device'])
        meas = Measure(temperature=temp, name=sensor['name'], timestamp=datetime.strptime(time, "%Y-%m-%d %H:%M:%S"))
        meas.print()

    temperatures_sources.append(meas)

    return temperatures_sources

def send_request(url: str, device:str):
    params = {
        "cmd": f"jsonlist2 {device}",
        "XHR": "1",
    }
    try:
        response = requests.post(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data.get("Results"), list) and data["Results"]:
                temperature = data["Results"][0].get("Readings", {}).get("temperature").get("Value")
                time = data["Results"][0].get("Readings", {}).get("temperature").get("Time")
            else:
                temperature = None
                time = None

            return temperature, time

        else:
            print(f"Request failed with status code {response.status_code}: {response.text}")
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
