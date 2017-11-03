#!/usr/bin/env python

import time
import paho.mqtt.client as paho
from datetime import datetime

import socket

carbon_sock = None
CARBON_SERVER = '0.0.0.0'
CARBON_PORT = 2003

MQTT_CLIENT_NAME = 'raspberry_consumer_client'
MQTT_HOST = '127.0.0.1'
MQTT_SUBSRIBER_TOPIC = "home/#"

print("Start script")


def send_to_carbon(topic, value):
    global carbon_sock
    if carbon_sock is None:
        carbon_sock = socket.socket()
        carbon_sock.connect((CARBON_SERVER, CARBON_PORT))
    message = '%s %s %d\n' % (topic, value, int(time.time()))
    carbon_sock.sendall(message)
    print("%s Sent: topic[%s], value:[%s]" % (datetime.now(), topic, value))


def on_message(client, userdata, message):

    try:
        val = float(message.payload)
    except ValueError:
        return
    send_to_carbon(message.topic.replace('/', '.'), val)

client = paho.Client(MQTT_CLIENT_NAME)
client.on_message = on_message
client.connect(MQTT_HOST)
client.loop_start()

client.subscribe(MQTT_SUBSRIBER_TOPIC)
time.sleep(999999999)
