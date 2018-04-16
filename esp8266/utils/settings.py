import ujson as json


class Settings():
    WIFI_SSID = ""
    WIFI_PASS = ""


with open('/config.json') as f:
    for k, v in json.load(f).items():
        if hasattr(Settings, k):
            setattr(Settings, k, v)
            print("set %s=%s" % (k, v))
        else:
            print("WARNING: Unknown config option (%s=%s)" % (k, v))
