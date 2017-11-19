import time
import network

import dht
import machine
import ubinascii
from machine import Pin
from umqtt.simple import MQTTClient


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
        if topic == "humidifier":
            client.publish('home/%s/state_humidifier' % _client_id, mqtt_val(10))
        elif topic == 'lamp':
            client.publish('home/%s/state_lamp' % _client_id, mqtt_val(5))
    elif msg == "off":
        pin.off()
        if topic == "humidifier":
            client.publish('home/%s/state_humidifier' % _client_id, mqtt_val(0))
        elif topic == 'lamp':
            client.publish('home/%s/state_lamp' % _client_id, mqtt_val(0))
    else:
        print("Unknown command %s" % msg)


on_message(b'humidifier', b'on')
on_message(b'lamp', b'on')
time.sleep(5)
on_message(b'humidifier', b'off')
on_message(b'lamp', b'off')
client.set_callback(on_message)
client.subscribe("home/relay/#")


def push_meassure(last_value):
    dht_pin = dht.DHT22(machine.Pin(14))  # D5
    dht_pin.measure()

    client.publish('home/%s/dht_t' % _client_id, mqtt_val(dht_pin.temperature()))
    client.publish('home/%s/dht_h' % _client_id, mqtt_val(dht_pin.humidity()))
    client.publish('home/%s/light' % _client_id, mqtt_val(machine.ADC(0).read()))

    #  if machine.Pin(4, machine.Pin.IN).value():  # D2
        #  client.publish('home/%s/state_window' % _client_id, mqtt_val(0))  # opened window
    #  else:
        #  client.publish('home/%s/state_window' % _client_id, mqtt_val(15))  # closed

try:
    while True:
        if not wlan.isconnected():
            machine.reset()
        push_meassure()
        print("wait_msg")
        for i in range(100):
            client.check_msg()
        time.sleep(10)
finally:
    client.disconnect()
