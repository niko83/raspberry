import network
import time
import machine

from utils.settings import Settings
import ubinascii
from umqtt.simple import MQTTClient



def mqtt_val(val):
    return bytes(str(val), 'utf-8')

rtc = machine.RTC()
rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)


def deepsleep():
    time.sleep_ms(300)
    rtc.alarm(rtc.ALARM0, deepsleep_interval)
    print("machine is going to deeplseep")
    machine.deepsleep()


class PIN:
    D0 = 16  # build-in led
    D1 = 5
    D2 = 4
    D3 = 0
    D4 = 2
    D5 = 14
    D6 = 12
    D7 = 13
    D8 = 15
    D9 = 3
    D10 = 1
    map_to_d = {
        16: 'D0',
        5: 'D1',
        4: 'D2',
        0: 'D3',
        2: 'D4',
        14: 'D5',
        12: 'D6',
        13: 'D7',
        15: 'D8',
        3: 'D9',
        1: 'D10',
    }
    str_to_pin = dict((v, k) for k, v in map_to_d.items())


for p in PIN.map_to_d.keys():
    machine.Pin(PIN.D8, machine.Pin.OUT).off()

network.WLAN(network.AP_IF).active(False)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(Settings.WIFI_SSID, Settings.WIFI_PASS)


client_id = ubinascii.hexlify(machine.unique_id()).decode("utf-8")
print("Client_id: %s" % client_id)


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
        client = MQTTClient(client_id, Settings.MQTT_IP)
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

    if time.time() - _last_heartbit > 300:
        return 'ERROR'
