import network
import machine
import time
from umqtt.simple import MQTTClient

CONFIG = {
    "broker": "",
    "wifi_ssid": "",
    "wifi_pass": "",
    "sensor_pin": 0,
    "client_id": "nodemcu1",
    "topic": "home",
}


def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(CONFIG['wifi_ssid'], CONFIG['wifi_pass'])
    print('Connecting to network...')
    if not wlan.isconnected():
        time.sleep(1)
    print('Connected:', wlan.ifconfig())

client = None
sensor_pin = None


def setup_pins():
    global sensor_pin
    sensor_pin = machine.ADC(CONFIG['sensor_pin'])


def load_config():
    import ujson as json
    try:
        with open("/config.json") as f:
            config = json.loads(f.read())
    except (OSError, ValueError):
        print("Couldn't load /config.json")
    else:
        CONFIG.update(config)
        print("Loaded config from /config.json")


def main():
    time.sleep(5)
    client = MQTTClient(CONFIG['client_id'], CONFIG['broker'])
    client.connect()
    print("Connected to {}".format(CONFIG['broker']))
    while True:
        data = sensor_pin.read()
        client.publish(
            '{}/{}'.format(CONFIG['topic'], CONFIG['client_id']),
            bytes(str(data), 'utf-8')
        )
        print('Sensor state: {}'.format(data))
        time.sleep(5)


if __name__ == '__main__':
    load_config()
    do_connect()
    setup_pins()
    main()
