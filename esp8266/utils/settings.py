import ujson as json
from lib.logging import getLogger
log = getLogger(__name__)

_config_file = '/config.json'


class Config():
    WIFI_SSID = ""
    WIFI_PASS = ""
    IP = None

    MQTT_BROKER = ""
    MQTT_CLIENT_ID = None
    MQTT_SUBSCRIBER = False
    MQTT_TOPIC_PREFIX = "home"

    ANALOG_INPUT = ""
    DHT22_PIN = None

    @classmethod
    def load(cls):
        try:
            with open(_config_file) as f:
                config = json.load(f)
        except (OSError, ValueError):
            log.error('Couldn\'t load "%s"' % _config_file)
            raise

        for k, v in config.items():
            if hasattr(cls, k):
                setattr(cls, k, v)
            else:
                log.warning("config file has unknown attr: %s:%s", k, v)
