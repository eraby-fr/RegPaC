import requests

def send_heat(config: dict, enable: bool):
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
            return True
            #print(f"Request successful: {response}")
        else:
            print(f"Request failed with status code {response.status_code}: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return False
