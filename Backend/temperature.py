import random

def collect_temperatures():
    temperatures_sources = {
        "source1": 0.0,
        "source2": 0.0,
        "source3": 0.0
    }
        
    # Simuler la collecte des températures des sondes
    temperatures_sources["source1"] = random.uniform(18.0, 25.0)
    temperatures_sources["source2"] = random.uniform(18.0, 25.0)
    temperatures_sources["source3"] = random.uniform(18.0, 25.0)

    return temperatures_sources