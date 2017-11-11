import time
import network

import dht
import machine
import ubinascii
from umqtt.simple import MQTTClient


def calculate_real_value(val, _type=None):
    if _type != 'temp':
        return 1024 - float(val)
    elif _type == 'temp':
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


def mqtt_val(val):
    return bytes(str(val), 'utf-8')

network.WLAN(network.AP_IF).active(False)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("", "")
c = 0
while True:
    if wlan.isconnected():
        break
    c += 1
    print(c)
    time.sleep(1)
    if c > 30:
        machine.reset()
print(wlan.ifconfig())

_client_id = ubinascii.hexlify(machine.unique_id()).decode("utf-8")
c = 0
while True:
    try:
        client = MQTTClient(_client_id, "192.168.100.12")
        client.connect()
        break
    except:
        time.sleep(1)
        c += 1
        if c > 30:
            machine.reset()
print("Successfully Connected to MQTT")


dht_pin = dht.DHT22(machine.Pin(14))
dht_pin.measure()
client.publish('home/%s/dht_t' % _client_id, mqtt_val(dht_pin.temperature()))
client.publish('home/%s/dht_h' % _client_id, mqtt_val(dht_pin.humidity()))
client.publish('home/%s/light' % _client_id, mqtt_val(calculate_real_value(machine.ADC(0).read())))

time.sleep(0.5)
rtc = machine.RTC()
rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
rtc.alarm(rtc.ALARM0, 300000)

print("Going to deepsleep. Bye...")
machine.deepsleep()
