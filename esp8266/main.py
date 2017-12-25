import time
import network

import dht
import machine
import ubinascii
from machine import Pin
from umqtt.simple import MQTTClient


def mqtt_val(val):
    return bytes(str(val), 'utf-8')


class PIN:
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


def push_meassure():
    for pin in [
        PIN.D5,
        PIN.D6,
        #  PIN.D7,
        #  PIN.D8,
    ]:
        dht_pin = dht.DHT22(machine.Pin(pin))
        dht_pin.measure()
        client.publish(
            'home/%s/dht_t_%s' % (_client_id, PIN.map_to_d[pin]),
            mqtt_val(dht_pin.temperature())
        )
        client.publish(
            'home/%s/dht_h_%s' % (_client_id, PIN.map_to_d[pin]),
            mqtt_val(dht_pin.humidity())
        )

    #  client.publish('home/%s/plant' % _client_id, mqtt_val(machine.ADC(0).read()))

    #  if machine.Pin(4, machine.Pin.IN).value():  # D2
        #  client.publish('home/%s/state_window' % _client_id, mqtt_val(0))  # opened window
    #  else:
        #  client.publish('home/%s/state_window' % _client_id, mqtt_val(15))  # closed

try:
    while True:
        if not wlan.isconnected():
            machine.reset()
        push_meassure()
        time.sleep(10)
finally:
    client.disconnect()

#  time.sleep(0.5)
#  rtc = machine.RTC()
#  rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
#  rtc.alarm(rtc.ALARM0, 300000)

#  print("Going to deepsleep. Bye...")
#  machine.deepsleep()
