import ujson as json


class Settings():
    WIFI = []
    WIFI_AP_ENABLED = False
    WIFI_AP = ["", ""]
    MQTT_IP = ""
    DHTs = []
    DS18pins = []
    SI7021 = []
    PLANT = None   # EXAMPLE {"relay_pin": 'd8', 'power_pin': 'd2', 'limit_wet': 65}
    ENABLED_DEEPSLEEP = False
    INTERVAL = 30000


with open('/config.json') as f:
    for k, v in json.load(f).items():
        if hasattr(Settings, k):
            setattr(Settings, k, v)
            print("OK: set %s=%s" % (k, v))

        else:
            print("WARNING: Unknown config option (%s=%s)" % (k, v))
    print("===================")
