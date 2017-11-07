import machine
from machine import Pin
import time
from lib import logging
from utils.settings import Config
from utils import wifi, mqtt
from utils.analog_sensor import calculate_real_value
from umqtt.simple import MQTTClient
import dht


rtc = machine.RTC()
rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
rtc.alarm(rtc.ALARM0, 120000)  # 2 min

log = logging.getLogger('main')


def on_message(topic, msg):
    topic = topic.decode('utf-8')
    msg = msg.decode('utf-8')
    topic = topic.split('/')[-1]
    if topic == "humidifier":
        pin = machine.Pin(12, Pin.OUT)
    elif topic == "lamp":
        pin = machine.Pin(13, Pin.OUT)
    else:
        log.warning('Unknown topic "%s"' % topic)
        return

    if msg == "on":
        pin.on()
    elif msg == "off":
        pin.off()
    else:
        log.warning("Unknown command %s" % msg)


def publish_analog():
    mqtt.publish(Config.ANALOG_INPUT, calculate_real_value(machine.ADC(0).read()))


def dht22_processing(pin):
    if pin is None:
        return

    dht_pin = dht.DHT22(machine.Pin(pin))
    dht_pin.measure()
    mqtt.publish('dht_t', dht_pin.temperature())
    mqtt.publish('dht_h', dht_pin.humidity())

if __name__ == '__main__':
    logging.basicConfig(stream="/main.log")
    log.info("Starting.")

    Config.load()
    wifi.do_connect()

    try:
        publish_analog()
        dht22_processing(Config.DHT22_PIN)
    except Exception as e:
        log.error('Sensor exception: %s', e)

    mqtt.get_client().disconnect()
    wifi.disconnect()
    log.info("DEEPLEEP")
    machine.deepsleep()

    #  if Config.SUBSCRIBER:
        #  try:
            #  while True:
                #  client.wait_msg()
        #  except Exception as e:
            #  log.warning("wait msg exception: %s" % e)
            #  machine.reset()
            #  return

#  machine.Pin(12, Pin.OUT).off()
#  machine.Pin(13, Pin.OUT).off()

    #  if Config.SUBSCRIBER:
        #  client.set_callback(on_message)
        #  client.subscribe("home/relay/#")
