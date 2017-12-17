#!/usr/bin/env python

import time
from wsgiref import simple_server
import falcon
import sys
import paho.mqtt.client as paho
import threading


_lock = threading.Lock()

MQTT_CLIENT_NAME = 'raspberry_consumer_client'
MQTT_HOST = '127.0.0.1'
MQTT_SUBSRIBER_TOPIC = "home/#"

print("----------------------")
print("Start script")
print("----------------------")

last_values = {}

NORMALIZATORS = {
    'dht_t': lambda x: round(x/2, 1)*2,
    'dht_h': round,
    'light': lambda x: round((1024.0 - x)/1024/0.02) * 2,
    'plant': lambda x: round((1024.0 - x)/1024/0.01),
}


def DEFAULT_NORMALIZATOR(x):
    return x


def processing():
    client = paho.Client(MQTT_CLIENT_NAME)
    client.connect(MQTT_HOST)
    humitidy_processing()


def humitidy_processing():
    gisteresis = 2
    humidity_limit = 50
    key = '370c3800'
    last_humidity = last_values.get("home.%s.dht_h" % key)
    last_temperature = last_values.get("home.%s.dht_t" % key)
    if (
        last_temperature is None or
        last_humidity is None or
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


def on_message(client, userdata, message):
    if "home/relay" in message.topic:
        return

    print("get. Topic: %s Payload:%s" % (message.topic, message.payload))
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

    _lock.acquire()
    try:
        last_values[message.topic] = (normalizator(value), time.time())
    finally:
        _lock.release()


client = paho.Client(MQTT_CLIENT_NAME)
client.on_message = on_message
client.connect(MQTT_HOST)
client.loop_start()

client.subscribe(MQTT_SUBSRIBER_TOPIC)


def _metric(metric_name, val, time, **labels):
    labels_str = ''
    if labels:
        labels_list = []
        for name, l_val in labels.items():
            labels_list.append('%s="%s"' % (name, l_val))
        labels_str = "{" + ','.join(labels_list) + "}"

    return "%s%s %s %s000" % (metric_name, labels_str, val, int(time))


class ThingsResource(object):
    def on_get(self, req, resp):
        _lock.acquire()
        processing()
        try:
            data = []
            for key, (value, _time) in last_values.items():

                try:
                    namespace, wifipoint, _type = key.split('/', 2)
                except ValueError:
                    print("error: %s" % key)
                    last_values.pop(key)
                    continue
                data.append(_metric('val', value, _time, **{
                    'namespace': namespace,
                    'wifipoint': wifipoint,
                    'type': _type,
                }))
                last_values.pop(key)
        finally:
            _lock.release()

        resp.body = "\n".join(data)

app = falcon.API()
app.add_route('/metrics', ThingsResource())
httpd = simple_server.make_server('127.0.0.1', 8000, app)
httpd.serve_forever()
