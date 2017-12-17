#!/usr/bin/env python

import time
import sys
import paho.mqtt.client as paho
from locker import one_thread_restriction
import settings
import logging

logger = logging.getLogger("smarthome")


MQTT_CLIENT_NAME = 'raspberry_consumer_client'
MQTT_HOST = '127.0.0.1'
MQTT_SUBSRIBER_TOPIC = "home/#"


last_values = {}

NORMALIZATORS = {
    'dht_t': lambda x: round(x/2, 1)*2,
    'dht_h': round,
    'light': lambda x: round((1024.0 - x)/1024/0.02) * 2,
    'plant': lambda x: round((1024.0 - x)/1024/0.01),
}


def DEFAULT_NORMALIZATOR(x):
    return x


@one_thread_restriction(settings.LOCK_KEY)
def on_message(client, userdata, message):
    print("Topic: %s Payload:%s" % (message.topic, message.payload))

    if "home/relay" in message.topic:
        return

    sys.stdout.flush()

    try:
        value = float(message.payload)
    except ValueError:
        print("Skipped not float")
        return

    normalizator = NORMALIZATORS.get(
        message.topic.split('/')[-1],
        DEFAULT_NORMALIZATOR
    )

    last_values[message.topic] = (normalizator(value), time.time())


client = paho.Client(MQTT_CLIENT_NAME)
client.on_message = on_message
while True:
    try:
        client.connect(MQTT_HOST)
        break
    except Exception as e:
        logger.error("Can not connect to mqtt %s", MQTT_HOST)
        time.sleep(5)

client.subscribe(MQTT_SUBSRIBER_TOPIC)
client.loop_forever()
