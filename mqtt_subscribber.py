#!/usr/bin/env python

import time
import paho.mqtt.client as paho

import socket

carbon_sock = None
CARBON_SERVER = '0.0.0.0'
CARBON_PORT = 2003

MQTT_CLIENT_NAME = 'raspberry_consumer_client'
MQTT_HOST = '127.0.0.1'
MQTT_SUBSRIBER_TOPIC = "home/#"


def send_to_carbon(topic, value):
    global carbon_sock
    if carbon_sock is None:
        carbon_sock = socket.socket()
        carbon_sock.connect((CARBON_SERVER, CARBON_PORT))
    message = '%s %s %d\n' % (value, int(time.time()))
    carbon_sock.sendall(message)
    print("Send: topic[%s], value:[%s]" % (topic, value))


def on_message(client, userdata, message):
    send_to_carbon(
        message.topic.replace('/', '.'),
        float(message.payload)
    )

client = paho.Client(MQTT_CLIENT_NAME)
client.on_message = on_message
client.connect(MQTT_HOST)
client.loop_start()

client.subscribe(MQTT_SUBSRIBER_TOPIC)
time.sleep(999999999)
