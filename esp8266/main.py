import network
import machine
from machine import Pin
import time
from umqtt.simple import MQTTClient
import dht

network.WLAN(network.AP_IF).active(False)

rtc = machine.RTC()
rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
rtc.alarm(rtc.ALARM0, 120000)  # 2 min
machine.Pin(12, Pin.OUT).off()
machine.Pin(13, Pin.OUT).off()


CONFIG = {
    "broker": "",
    "wifi_ssid": "",
    "wifi_pass": "",
    "client_id": None,
    "topic": "home",
    "analog_input": "",
    "dht22_pin": None,
    "subscriber": False,
}


def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(CONFIG['wifi_ssid'], CONFIG['wifi_pass'])
    print('Connecting to network...')
    print('Connected to network:', wlan.ifconfig())


def load_config():
    import ujson as json
    try:
        with open("/config.json") as f:
            config = json.loads(f.read())
    except (OSError, ValueError):
        print("Couldn't load /config.json")
    else:
        CONFIG.update(config)


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


def get_mqtt_client(limit_seconds=15):
    client = MQTTClient(CONFIG['client_id'], CONFIG['broker'])
    sleep = 0.5
    limit = int(limit_seconds / sleep)
    while limit > 0:
        try:
            time.sleep(0.5)

            if CONFIG['subscriber']:
                client.set_callback(on_message)
                client.connect()
                client.subscribe("home/relay/#")
            else:
                client.connect()

            print("Connected to MQTT {}".format(CONFIG['broker']))
            return client
        except Exception as e:
            limit -= 1
            print("Connect to mqtt failed: (left attempts %s) %s %s" % (limit, type(e), e))

    machine.deepsleep()


def publish_analog(client, sensor_pin):
    client.publish(
        '{}/{}/{}'.format(CONFIG['topic'], CONFIG['client_id'], CONFIG['analog_input']),
        bytes(str(calculate_real_value(sensor_pin.read())), 'utf-8')
    )


def publish_dht22(client, dht_pin):
    if CONFIG['dht22_pin'] is None:
        return
    dht_pin.measure()
    client.publish(
        '{}/{}/dht_t'.format(CONFIG['topic'], CONFIG['client_id']),
        bytes(str(dht_pin.temperature()), 'utf-8')
    )
    client.publish(
        '{}/{}/dht_h'.format(CONFIG['topic'], CONFIG['client_id']),
        bytes(str(dht_pin.humidity()), 'utf-8')
    )


def on_message(topic, msg):
    topic = topic.decode('utf-8')
    msg = msg.decode('utf-8')
    topic = topic.split('/')[-1]
    if topic == "humidifier":
        pin = machine.Pin(12, Pin.OUT)
    elif topic == "lamp":
        pin = machine.Pin(13, Pin.OUT)
    else:
        print('Unknown topic "%s"' % topic)
        return

    if msg == "on":
        pin.on()
    elif msg == "off":
        pin.off()
    else:
        print("Unknown command %s" % msg)


def main():
    client = get_mqtt_client()

    if CONFIG['subscriber']:
        print('1')
        try:
            while True:
                print('2')
                client.wait_msg()
                print('3')
        except Exception as e:
            print("wait msg exception: %s" % e)
            return

    analog_pin = machine.ADC(0)
    if CONFIG['dht22_pin'] is not None:
        dht_pin = dht.DHT22(machine.Pin(CONFIG['dht22_pin']))

    while True:
        try:
            publish_analog(client, analog_pin)
            publish_dht22(client, dht_pin)
        except Exception as e:
            print('Sensor exception: %s' % e)

        time.sleep(0.2)  # waiting for sent last client.publish
        client.disconnect()
        machine.deepsleep()
        time.sleep(10)

if __name__ == '__main__':
    load_config()
    do_connect()
    main()
