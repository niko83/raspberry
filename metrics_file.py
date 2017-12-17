import json
import settings

def read():
    try:
        with open(settings.METRICS_FILE, 'w+') as f:
            return json.load(f)
    except:
        return {}


def write(data):
    with open(settings.METRICS_FILE, 'w+') as f:
        return json.dump(f, data)
