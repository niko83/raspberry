import time

import dht
import machine
from machine import Pin
from utils import client_id, client, PIN, mqtt_val, check_heartbit


def on_message(topic, msg):
    if check_heartbit (topic) == 'ERROR':
        machine.reset()

    topic = topic.decode('utf-8')
    msg = msg.decode('utf-8')
    topic = topic.split('/')[-1]
    if topic == "humidifier":
        pin = machine.Pin(PIN.D6, Pin.OUT)
    elif topic == "lamp":
        pin = machine.Pin(PIN.D7, Pin.OUT)
    else:
        print('Unknown topic "%s"' % topic)
        return

    if msg == "on":
        pin.on()
        if topic == "humidifier":
            client.publish('home/%s/state_humidifier' % client_id, mqtt_val(10))
        elif topic == 'lamp':
            client.publish('home/%s/state_lamp' % client_id, mqtt_val(5))
    elif msg == "off":
        pin.off()
        if topic == "humidifier":
            client.publish('home/%s/state_humidifier' % client_id, mqtt_val(0))
        elif topic == 'lamp':
            client.publish('home/%s/state_lamp' % client_id, mqtt_val(0))
    else:
        print("Unknown command %s" % msg)

plant_pin_vc = machine.Pin(PIN.D2, Pin.OUT)
plant_pin_vc.off()
#  on_message(b'humidifier', b'on')
#  on_message(b'lamp', b'on')
#  time.sleep(5)
#  on_message(b'humidifier', b'off')
#  on_message(b'lamp', b'off')
client.set_callback(on_message)
client.subscribe("home/#")




def push_meassure():
    dht_pin = dht.DHT22(machine.Pin(PIN.D5))
    dht_pin.measure()

    client.publish('home/%s/dht_t' % client_id, mqtt_val(dht_pin.temperature()))
    client.publish('home/%s/dht_h' % client_id, mqtt_val(dht_pin.humidity()))

    plant_pin_vc.on()
    client.publish('home/%s/plant2' % client_id, mqtt_val(machine.ADC(0).read()))
    plant_pin_vc.off()

try:
    while True:
        push_meassure()
        for i in range(100):
            client.check_msg()
        time.sleep(10)
finally:
    machine.reset()
