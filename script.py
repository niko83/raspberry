#!/usr/bin/env python

import time
import paho.mqtt.client as paho

import socket


CARBON_SERVER = '0.0.0.0'
CARBON_PORT = 2003


sock = socket.socket()
sock.connect((CARBON_SERVER, CARBON_PORT))


def on_message(client, userdata, message):
    m = '%s %d %d\n' % (
        message.topic.replace('/', '.'),
        int(message.payload), 
        int(time.time()),
    )
        
    sock.sendall(m)
    print(m.replace('\n', ''))


client = paho.Client("client-001")
client.on_message = on_message
client.connect("127.0.0.1")
client.loop_start()

client.subscribe("home/#")
time.sleep(999999999)
