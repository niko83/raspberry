import time

import dht
import machine
import onewire
from utils.settings import Settings
from utils import PIN, client_id, client, mqtt_val, check_heartbit, deepsleep
import ds18x20
from utils.si7021 import Si7021


if Settings.ENABLED_DEEPSLEEP:
    reset = deepsleep
else:
    reset = machine.reset


def processing_dht(pin):
    dht_pin = dht.DHT22(machine.Pin(PIN.str_to_pin[pin]))
    dht_pin.measure()
    client.publish(
        'home/%s/dht_t_%s' % (client_id, pin),
        mqtt_val(dht_pin.temperature())
    )
    client.publish(
        'home/%s/dht_h_%s' % (client_id, pin),
        mqtt_val(dht_pin.humidity())
    )


def processing_d18(pin):
    # Measure onewire
    # ds = ds18x20.DS18X20(onewire.OneWire(machine.Pin(PIN.D5)));
    # room = ds.scan()[0]; ds.convert_temp(); time.sleep_ms(750); ds.read_temp(rom);

    ds = ds18x20.DS18X20(onewire.OneWire(machine.Pin(PIN.str_to_pin[pin])))
    roms = ds.scan()

    ds.convert_temp()
    time.sleep_ms(750)
    for rom in roms:
        client.publish(
            'home/%s/temperature_%s' % (client_id, pin),
            mqtt_val(ds.read_temp(rom))
        )


def processing_plant(relay_pin, power_pin, limit_wet):

    if relay_pin:
        relay_pin = machine.Pin(relay_pin, machine.Pin.OUT)

    plant_pin_vc = machine.Pin(power_pin, machine.Pin.OUT)

    plant_pin_vc.on()
    time.sleep_ms(5)
    wet = machine.ADC(0).read()
    client.publish('home/%s/plant' % client_id, mqtt_val(wet))
    plant_pin_vc.off()

    if relay_pin and limit_wet:
        if (1024.0 - wet) / 1024 * 100 < limit_wet:
            relay_pin.on()
            client.publish('home/%s/pump' % client_id, mqtt_val(10))
            time.sleep(5)
            relay_pin.off()
        else:
            relay_pin.off()
            client.publish('home/%s/pump' % client_id, mqtt_val(0))


def processing_si7021(scl, sda):
    si = Si7021(scl, sda)
    client.publish('home/%s/sht_h' % client_id, mqtt_val(si.readRH()))
    client.publish('home/%s/sht_t' % client_id, mqtt_val(si.readTemp()))


def push_meassure():

    for pin in Settings.DHTs:
        processing_dht(pin)

    # Measure analog
    if Settings.PLANT:
        processing_plant(**Settings.PLANT)

    for pin in Settings.DS18pins:
        processing_d18(pin)

    for scl, sda in Settings.SI7021:
        processing_si7021(scl, sda)


def on_message(topic, msg):
    if check_heartbit(topic) == 'ERROR':
        reset()

client.set_callback(on_message)
client.subscribe("home/#")

try:
    if reset is deepsleep:
        push_meassure()
        reset()
    else:
        while True:
            print("Iteration is starting...")
            push_meassure()
            for i in range(100):
                client.check_msg()
            time.sleep_ms(30000)
finally:
    reset()
