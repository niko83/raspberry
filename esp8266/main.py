import gc
print("Free mem: %s" % gc.mem_free())

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


def err_handler(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            print("FAIL[%s,%s] %s" % (args, kwargs, e))
            try:
                client.publish(
                    'home/%s/error_%s' % (client_id, "_".join(args)),
                    mqtt_val(1)
                )
            except Exception as e:
                print("While sending error to mqtt error accured: %s " % e)
        else:
            print("OK[%s,%s] = %s" % (args, kwargs, result))
    return wrapper


@err_handler
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


@err_handler
def processing_d18(pin):
    # Measure onewire
    # ds = ds18x20.DS18X20(onewire.OneWire(machine.Pin(PIN.D5)));
    # room = ds.scan()[0]; ds.convert_temp(); time.sleep_ms(750); ds.read_temp(rom);

    ds = ds18x20.DS18X20(onewire.OneWire(machine.Pin(PIN.str_to_pin[pin])))
    roms = ds.scan()

    ds.convert_temp()
    time.sleep_ms(750)
    v = ds.read_temp(roms[0])
    client.publish(
        'home/%s/temperature_%s' % (client_id, pin),
        mqtt_val(v)
    )
    return v



@err_handler
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


@err_handler
def processing_si7021(scl, sda):
    scl = PIN.str_to_pin[scl]
    sda = PIN.str_to_pin[sda]

    si = Si7021(scl, sda)
    h, t = si.readRH(), si.readTemp()
    client.publish('home/%s/sht_h' % client_id, mqtt_val(h))
    client.publish('home/%s/sht_t' % client_id, mqtt_val(t))
    return h, t


def push_meassure():

    for pin in Settings.DHTs:
        processing_dht(pin)

    # Measure analog
    if Settings.PLANT:
        processing_plant(**Settings.PLANT)

    for pin in Settings.DS18pins:
        try:
            processing_d18(pin)
        except Exception as e:
            print("FAil %s %s" %( pin, e))

    for scl, sda in Settings.SI7021:
        processing_si7021(scl, sda)


def on_message(topic, msg):
    if check_heartbit(topic) == 'ERROR':
        reset()

client.set_callback(on_message)
client.subscribe("home/#")

try:
    print("Free mem after init: %s" % gc.mem_free())
    if reset is deepsleep:
        push_meassure()
        reset()
    else:
        while True:
            print("Current free mem: %s" % gc.mem_free())
            print("Iteration is starting...")
            push_meassure()
            for i in range(100):
                client.check_msg()
            time.sleep_ms(Settings.INTERVAL)
finally:
    reset()
