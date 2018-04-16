import time

import dht
import machine
from utils import wlan, client_id, client, PIN, mqtt_val


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
            'home/%s/dht_t_%s' % (client_id, PIN.map_to_d[pin]),
            mqtt_val(dht_pin.temperature())
        )
        client.publish(
            'home/%s/dht_h_%s' % (client_id, PIN.map_to_d[pin]),
            mqtt_val(dht_pin.humidity())
        )

    #  client.publish('home/%s/plant' % client_id, mqtt_val(machine.ADC(0).read()))

    #  if machine.Pin(4, machine.Pin.IN).value():  # D2
        #  client.publish('home/%s/state_window' % client_id, mqtt_val(0))  # opened window
    #  else:
        #  client.publish('home/%s/state_window' % client_id, mqtt_val(15))  # closed

try:
    while True:
        if not wlan.isconnected():
            machine.reset()
        push_meassure()
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
