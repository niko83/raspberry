import time

import dht
import machine
from utils import wlan, client_id, client, PIN, mqtt_val, check_heartbit


plant_pin_vc = machine.Pin(PIN.D2, machine.Pin.OUT)
plant_pin_vc.off()

def push_meassure():
    for pin in [
        PIN.D5,
        #  PIN.D6,
        #  PIN.D7,
        #  PIN.D8,
    ]:
        dht_pin = dht.DHT22(machine.Pin(pin))
        dht_pin.measure()
        client.publish(
            'home/%s/dht_t_%s' % (client_id, PIN.map_to_d[pin]),
            mqtt_val(dht_pin.temperature())
        )
        client.publish(
            'home/%s/dht_h_%s' % (client_id, PIN.map_to_d[pin]),
            mqtt_val(dht_pin.humidity())
        )

    plant_pin_vc.on()
    client.publish('home/%s/plant' % client_id, mqtt_val(machine.ADC(0).read()))
    plant_pin_vc.off()


def on_message(topic, msg):
    if check_heartbit(topic) == 'ERROR':
        machine.reset()


client.set_callback(on_message)
client.subscribe("home/#")

try:
    while True:
        push_meassure()
        for i in range(100):
            client.check_msg()
        time.sleep(10)
finally:
    client.disconnect()
    machine.reset()

#  time.sleep(0.5)
#  rtc = machine.RTC()
#  rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
#  rtc.alarm(rtc.ALARM0, 300000)

#  print("Going to deepsleep. Bye...")
#  machine.deepsleep()
