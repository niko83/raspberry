#!/usr/bin/env python

import time
import paho.mqtt.client as paho
import datetime

import socket

carbon_sock = None
CARBON_SERVER = '0.0.0.0'
CARBON_PORT = 2003

MQTT_CLIENT_NAME = 'raspberry_consumer_client2'
MQTT_HOST = '127.0.0.1'

print("----------------------")
print("Start script")
print("----------------------")

cnt = 0
while True:
    client = paho.Client(MQTT_CLIENT_NAME)
    client.connect(MQTT_HOST)

    if datetime.time(19, 00) < datetime.datetime.now().time() < datetime.time(20, 30):
        print("on")
	client.publish("home/relay/lamp", "off");
    else: 
        print("off")
	client.publish("home/relay/lamp", "on");
    time.sleep(300)

