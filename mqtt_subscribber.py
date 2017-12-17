#!/usr/bin/env python

import time
from wsgiref import simple_server
import falcon
import sys
import os
import paho.mqtt.client as paho
from datetime import datetime
from datetime import timedelta
import threading
import signal

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

measure_min_delta = timedelta(seconds=10)

NORMALIZATORS = {
    'dht_t': lambda x: round(x/2, 1)*2,
    'dht_h': round,
    'light': lambda x: round((1024.0 - x)/1024/0.02) * 2,
    'plant': lambda x: round((1024.0 - x)/1024/0.01),
}


def DEFAULT_NORMALIZATOR(x):
    return x

_IS_RUNNING = True

def processing():
    client = paho.Client(MQTT_CLIENT_NAME + '2')
    client.connect(MQTT_HOST)
    while _IS_RUNNING:
	humitidy_processing()
	time.sleep(5)


def humitidy_processing():
    gisteresis = 2
    humidity_limit = 50
    key = '370c3800'
    #  while True:
    last_humidity = last_values.get("home.%s.dht_h" % key)
    last_temperature = last_values.get("home.%s.dht_t" % key)
    if (
        last_temperature is None or
        last_humidity is None or
        last_temperature[1] + measure_min_delta * 2 < datetime.now() or
        last_humidity[1] + measure_min_delta * 2 < datetime.now() or
        last_temperature[0] < 18.2 or
        last_humidity[0] > humidity_limit + gisteresis
    ):
        client.publish("home/relay/humidifier", "off")
        last_humidity = [None, None] if last_humidity is None else last_humidity
        last_temperature = [None, None] if last_temperature is None else last_temperature
        print("sent humidifier off (%s, %s)" % (last_humidity[0], last_temperature[0]))
        return

    if last_humidity[0] < humidity_limit:
        client.publish("home/relay/humidifier", "on")
        last_humidity = [None, None] if last_humidity is None else last_humidity
        last_temperature = [None, None] if last_temperature is None else last_temperature
        print("sent humidifier on (%s, %s)" % (last_humidity[0], last_temperature[0]))

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

    last_value = last_values.get(topic, [None, datetime.now()])
    if (
        last_value[0] != normalized_value or
        datetime.now() - last_value[1] > measure_min_delta
    ):
        carbon_sock.sendall('%s %s %d\n' % (topic, normalized_value, int(time.time())))
        print("Sent to carbon %s" % (normalized_value))
        last_values[topic] = (normalized_value, datetime.now())


def on_message(client, userdata, message):
    if "home/relay" in message.topic:
        return

    print("get. Topic: %s Payload:%s" % (message.topic, message.payload))
    sys.stdout.flush()

    try:
        val = float(message.payload)
    except ValueError:
        print("Skipped not float")
        return

    send_to_carbon(message.topic.replace('/', '.'), val)

client = paho.Client(MQTT_CLIENT_NAME)
client.on_message = on_message
client.connect(MQTT_HOST)
client.loop_start()

client.subscribe(MQTT_SUBSRIBER_TOPIC)


def signal_handler(signal, frame):
    global _IS_RUNNING
    print("stopping...")
    _IS_RUNNING = False

signal.signal(signal.SIGINT, signal_handler)
t = threading.Thread(target=processing)
t.setDaemon(True)
t.start()
time.sleep(999999999)

# class ThingsResource(object):
#     def on_get(self, req, resp):
#         """Handles GET requests"""
#         resp.status = falcon.HTTP_200  # This is the default status
#         resp.body = ('\nTwo things awe me most, the starry sky '
#                      'above me and the moral law within me.\n'
#                      '\n'
#                      '    ~ Immanuel Kant\n\n')
# 
# app = falcon.API()
# app.add_route('/metrics', ThingsResource())
# httpd = simple_server.make_server('127.0.0.1', 8000, app)
# httpd.serve_forever()
