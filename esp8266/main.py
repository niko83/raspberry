import machine
from machine import Pin
import time
from lib import logging
from utils.settings import Config
from utils import wifi, mqtt
from umqtt.simple import MQTTClient
import dht


rtc = machine.RTC()
rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
rtc.alarm(rtc.ALARM0, 60000)  # 2 min
machine.Pin(12, Pin.OUT).off()
machine.Pin(13, Pin.OUT).off()

log = logging.getLogger('main')




def publish_analog(client, sensor_pin):
    client.publish(
        '{}/{}/{}'.format(Config.TOPIC, Config.CLIENT_ID, Config.ANALOG_INPUT),
        bytes(str(calculate_real_value(sensor_pin.read())), 'utf-8')
    )


def publish_dht22(client, dht_pin):
    if Config.DHT22_PIN is None:
        return
    dht_pin.measure()
    client.publish(
        '{}/{}/dht_t'.format(Config.TOPIC, Config.CLIENT_ID),
        bytes(str(dht_pin.temperature()), 'utf-8')
    )
    client.publish(
        '{}/{}/dht_h'.format(Config.TOPIC, Config.CLIENT_ID),
        bytes(str(dht_pin.humidity()), 'utf-8')
    )


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


def main():
    client = get_mqtt_client()

    if Config.SUBSCRIBER:
        try:
            while True:
                client.wait_msg()
        except Exception as e:
            log.warning("wait msg exception: %s" % e)
            machine.reset()
            return

    analog_pin = machine.ADC(0)
    if Config.DHT22_PIN is not None:
        dht_pin = dht.DHT22(machine.Pin(Config.DHT22_PIN))

    while True:
        try:
            publish_analog(client, analog_pin)
            publish_dht22(client, dht_pin)
        except Exception as e:
            print('Sensor exception: %s' % e)

        time.sleep(0.2)  # waiting for sent last client.publish
        machine.sleep()

if __name__ == '__main__':
    logging.basicConfig(stream="/main.log")
    log.info("Starting.")

    Config.load()
    wifi.do_connect(Config.WIFI_SSID, Config.WIFI_PASS, Config.IP)
    mqtt_client = mqtt.get_client(Config.MQTT_CLIENT_ID, Config.MQTT_BROKER)

    mqtt_client.publish("home/asd/asd", "dd")
    while 1:
        time.sleep(1)

    #  if Config.SUBSCRIBER:
        #  client.set_callback(on_message)
        #  client.subscribe("home/relay/#")
