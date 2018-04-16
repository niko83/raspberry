import network
import time
import machine

from utils.settings import Settings
import ubinascii
from umqtt.simple import MQTTClient


def mqtt_val(val):
    return bytes(str(val), 'utf-8')


class PIN:
    D2 = 4
    D5 = 14
    D6 = 12
    D7 = 13
    D8 = 15
    map_to_d = {
        14: 'D5',
        12: 'D6',
        13: 'D7',
        15: 'D8',
    }


network.WLAN(network.AP_IF).active(False)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(Settings.WIFI_SSID, Settings.WIFI_PASS)


client_id = ubinascii.hexlify(machine.unique_id()).decode("utf-8")
print("CLient_id: %s" % client_id)


c = 0
while True:
    if wlan.isconnected():
        break
    c += 1
    print("wlan connect attemp:%s" % c)
    time.sleep(1)
    if c > 30:
        machine.reset()
print(wlan.ifconfig())


c = 0
while True:
    try:
        client = MQTTClient(client_id, "192.168.100.12")
        client.connect()
        break
    except:
        time.sleep(1)
        c += 1
        if c > 30:
            machine.reset()
print("Successfully Connected to MQTT")

_last_heartbit = time.time()


def check_heartbit(topic):
    global _last_heartbit
    topic = topic.decode('utf-8')
    topic = topic.split('/')[-1]
    if topic == "heartbit":
        _last_heartbit = time.time()

    if time.time() - _last_heartbit > 60:
        return 'ERROR'
