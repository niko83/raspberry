import json
import os
import settings

def read():
    try:
        with open(settings.METRICS_FILE, 'r') as f:
            return json.load(f)
    except (ValueError, IOError) as e:
        return {}


def write(data):
    with open(settings.METRICS_FILE, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=True)


def remove():
    if os.path.exists(settings.METRICS_FILE):
        os.remove(settings.METRICS_FILE)
