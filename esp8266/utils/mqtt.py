import machine
from umqtt.simple import MQTTClient
from lib import logging
from time import sleep
from utils.settings import Config
import ubinascii

log = logging.getLogger(__name__)

_client = None

_auto_connection_recheck = 120000

_client_id = ubinascii.hexlify(machine.unique_id())


def get_client(timeout=10000):
    global _client
    if _client is not None:
        return _client

    client = MQTTClient(_client_id, Config.MQTT_BROKER)

    while True:
        try:
            client.connect()
            log.info("Successfully Connected to MQTT %s:%s" % (_client_id, Config.MQTT_BROKER))
            _client = client
            return client
        except Exception as e:
            log.warning("Connect to mqtt failed. %s %s" % (type(e), e))
            sleep(0.2)


def publish(topic_key, val):
    c = get_client()
    c.publish(
        '{}/{}/{}'.format(
            Config.MQTT_TOPIC_PREFIX,
            Config.MQTT_CLIENT_ID,
            topic_key
        ),
        bytes(str(val), 'utf-8')
    )
    sleep(0.2)
