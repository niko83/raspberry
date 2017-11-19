#!/usr/bin/env python

import time
import paho.mqtt.client as paho
from datetime import datetime
from timedelta import timedelta

import socket

carbon_sock = None
CARBON_SERVER = '0.0.0.0'
CARBON_PORT = 2003

MQTT_CLIENT_NAME = 'raspberry_consumer_client'
MQTT_HOST = '127.0.0.1'
MQTT_SUBSRIBER_TOPIC = "home/#"

print("----------------------")
print("Start script")
print("----------------------")

last_values = {}

measure_min_delta = timedelta(seconds=300)

NORMALIZATORS = {
    'dht_t': lambda x: round(x/2, 1)*2,
    'dht_h': round,
    'light': lambda x: round((1024 - x)/1024/2) * 2,
}


def DEFAULT_NORMALIZATOR(x):
    return x


def processing():
    humitidy_processing()


def humitidy_processing():
    gisteresis = 2
    humidity_limit = 50
    key = 'asd'
    #  while True:
    last_humidity = last_values.get("home.%s.dht_h" % key)
    last_temperature = last_values.get("home.%s.dht_t" % key)
    if (
        last_temperature is None or
        last_humidity is None or
        last_temperature[1] + measure_min_delta * 2 < datetime.now() or
        last_humidity[1] + measure_min_delta * 2 < datetime.now() or
        last_temperature[0] < 20 or
        last_humidity[0] > humidity_limit + gisteresis
    ):
        client.publish("home/relay/humidifier", "off")
        return

    if last_humidity[0] < humidity_limit:
        client.publish("home/relay/humidifier", "on")
        return


def send_to_carbon(topic, value):

    normalizator = NORMALIZATORS.get(
        topic.split('.')[-1],
        DEFAULT_NORMALIZATOR
    )

    global carbon_sock
    if carbon_sock is None:
        carbon_sock = socket.socket()
        carbon_sock.connect((CARBON_SERVER, CARBON_PORT))

    normalized_value = normalizator(value)

    last_value = last_values.get(topic, [None, None])
    if (
        last_value[0] != normalized_value or
        datetime.now() - last_value[1] > measure_min_delta
    ):
        carbon_sock.sendall('%s %s %d\n' % (topic, normalized_value, int(time.time())))
        print("Sent to carbon. Delta(%s)" % datetime.now() - last_value[1])
        last_values[topic] = (normalized_value, datetime.now())
    else:
        print("Skipped sent to carbon.")


def on_message(client, userdata, message):
    print("Get topic: %s  payload:%s" % (message.topic, message.payload))

    try:
        val = float(message.payload)
    except ValueError:
        print("Skipped")
        return

    send_to_carbon(message.topic.replace('/', '.'), val)
    processing()

client = paho.Client(MQTT_CLIENT_NAME)
client.on_message = on_message
client.connect(MQTT_HOST)
client.loop_start()

client.subscribe(MQTT_SUBSRIBER_TOPIC)
time.sleep(999999999)
