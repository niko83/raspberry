import network
import machine
import time
from umqtt.simple import MQTTClient
from machine import Pin
import dht

network.WLAN(network.AP_IF).active(False)

CONFIG = {
    "broker": "",
    "wifi_ssid": "",
    "wifi_pass": "",
    "client_id": None,
    "topic": "home",
    "analog_input": "",
    "dht22_pin": None,
}


def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(CONFIG['wifi_ssid'], CONFIG['wifi_pass'])
    print('Connecting to network...')
    if not wlan.isconnected():
        time.sleep(1)
    print('Connected:', wlan.ifconfig())


sensor_pin = machine.ADC(0)


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


def calculate_real_value(val):
    if CONFIG['analog_input'] != 'temp':
        return 1024 - float(val)
    elif CONFIG['analog_input'] == 'temp':
        val = float(val)
        calibr = (
            (1024, -30),
            (940, -25),
            (720, 5.6),
            (560, 22),
            (430, 36),
            (176, 100),
            (0, 150),
        )
        for i in range(len(calibr)):
            if val < calibr[i][0] and val >= calibr[i+1][0]:
                return (
                    (calibr[i][1] - calibr[i+1][1]) *
                    (val - calibr[i+1][0]) /
                    (calibr[i][0] - calibr[i+1][0])
                ) + calibr[i+1][1]


def main():
    client = MQTTClient(CONFIG['client_id'], CONFIG['broker'])
    time.sleep(5)
    client.connect()
    print("Connected to {}".format(CONFIG['broker']))
    pin = Pin(14, Pin.IN)
    dht_pin = None
    if CONFIG['dht22_pin'] is not None:
        dht_pin = dht.DHT22(machine.Pin(CONFIG['dht22_pin']))

    while True:
        time.sleep(3)
        try:
            data = calculate_real_value(sensor_pin.read())
            move = pin.value()
            client.publish(
                '{}/{}/{}'.format(CONFIG['topic'], CONFIG['client_id'], CONFIG['analog_input']),
                bytes(str(data), 'utf-8')
            )
            client.publish(
                '{}/{}/move'.format(CONFIG['topic'], CONFIG['client_id']),
                bytes(str(move), 'utf-8')
            )
            temp = None
            humidity = None
            if dht_pin:
                dht_pin.measure()
                temp = dht_pin.temperature()
                humidity = dht_pin.humidity()
                client.publish(
                    '{}/{}/dht_t'.format(CONFIG['topic'], CONFIG['client_id']),
                    bytes(str(temp), 'utf-8')
                )
                client.publish(
                    '{}/{}/dht_h'.format(CONFIG['topic'], CONFIG['client_id']),
                    bytes(str(humidity), 'utf-8')
                )

            print('Sensor state: {} {} DHT:{}C {}%'.format(move, data, temp, humidity))
        except Exception as e:
            print(e)


if __name__ == '__main__':
    load_config()
    do_connect()
    main()
