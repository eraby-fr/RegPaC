import random

def collect_temperatures():
    temperatures_sources = {
        "1": 0.0,
        "2": 0.0,
        "3": 0.0
    }
        
    # Simuler la collecte des températures des sondes
    temperatures_sources["1"] = random.uniform(18.0, 25.0)
    temperatures_sources["2"] = random.uniform(18.0, 25.0)
    temperatures_sources["3"] = random.uniform(18.0, 25.0)

    return temperatures_sources