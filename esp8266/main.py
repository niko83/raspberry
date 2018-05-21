import time

import dht
import machine
import onewire
from utils import client_id, client, PIN, mqtt_val, check_heartbit
import ds18x20


relay_1_pin = machine.Pin(PIN.D8, machine.Pin.OUT)
relay_1_pin.off()

relay_2_pin = machine.Pin(PIN.D7, machine.Pin.OUT)
relay_2_pin.off()

plant_pin_vc = machine.Pin(PIN.D2, machine.Pin.OUT)
plant_pin_vc.off()

rtc = machine.RTC()
rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)

deepsleep_interval = 30000


def push_meassure():
    for pin in [
        PIN.D5,
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

    # Measure analog
    plant_pin_vc.on()
    time.sleep_ms(5)
    wet = machine.ADC(0).read()
    client.publish('home/%s/plant' % client_id, mqtt_val(wet))
    plant_pin_vc.off()

    if (1024.0 - wet) / 1024 * 100 < 50:
        relay_1_pin.on()
        client.publish('home/%s/pump' % client_id, mqtt_val(10))
        time.sleep(30)
        relay_1_pin.off()
    else:
        relay_1_pin.off()
        client.publish('home/%s/pump' % client_id, mqtt_val(0))

    # Measure onewire
    for pin in [
        PIN.D6,
    ]:
        ds = ds18x20.DS18X20(onewire.OneWire(machine.Pin(pin)))
        roms = ds.scan()

        ds.convert_temp()
        time.sleep_ms(750)
        for rom in roms:
            client.publish(
                'home/%s/temperature_%s' % (client_id, PIN.map_to_d[pin]),
                 mqtt_val(ds.read_temp(rom))
            )


def on_message(topic, msg):
    if check_heartbit(topic) == 'ERROR':
        #  machine.reset()
        rtc.alarm(rtc.ALARM0, deepsleep_interval)
        print("machine is going to deeplseep")
        machine.deepsleep()

client.set_callback(on_message)
client.subscribe("home/#")

try:
    #  while True:
    push_meassure()
        #  for i in range(100):
            #  client.check_msg()
        #  time.sleep(10)

    time.sleep_ms(300)
    rtc.alarm(rtc.ALARM0, deepsleep_interval)
    print("machine is going to deeplseep")
    machine.deepsleep()
finally:
    #  machine.reset()
    rtc.alarm(rtc.ALARM0, deepsleep_interval)
    print("machine is going to deeplseep")
    machine.deepsleep()
