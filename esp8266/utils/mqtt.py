import machine
from umqtt.simple import MQTTClient
from lib import logging
from time import sleep

log = logging.getLogger(__name__)

_client = None

_auto_connection_recheck = 120000


def check_connection():
    if _client is not None:
        try:
            _client.ping()
            _client.publish('home/%s/ping' % _client_id, 1)
            log.info('MQTT connection OK.')
        except Exception as e:
            log.warning('MQTT connection failed (%s). RESET.', e)
            machine.reset()


def get_client(client_id, broker, timeout=10000):
    global _client, _client_id
    if _client is not None:
        return _client

    _client_id = client_id

    client = MQTTClient(_client_id, broker)

    tim = machine.Timer(-1)
    tim.init(
        period=timeout,
        mode=machine.Timer.ONE_SHOT,
        callback=lambda t: check_connection(),
    )

    while True:
        try:
            client.connect()
            log.info("Connected to MQTT %s:%s" % (client_id, broker))
            _client = client
            tim.init(
                period=_auto_connection_recheck,
                mode=machine.Timer.PERIODIC,
                callback=lambda t: check_connection(),
            )
            return client
        except Exception as e:
            log.warning("Connect to mqtt failed. %s %s" % (type(e), e))
            sleep(0.2)
