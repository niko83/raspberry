#!/usr/bin/env python

import time
from wsgiref import simple_server
import falcon
import sys
import paho.mqtt.client as paho
import threading
from pprint import pprint
import logging
logger = logging.getLogger()


_lock = threading.Lock()

MQTT_CLIENT_NAME = 'smarthome_client'
MQTT_HOST = '127.0.0.1'
MQTT_SUBSRIBER_TOPIC = "home/#"

last_values = {}

NORMALIZATORS = {
    "plant": lambda x: (1024.0 - x)/1024*100,
    "plant2": lambda x: (1024.0 - x)/1024*100,
}


def DEFAULT_NORMALIZATOR(x):
    return x


def processing():
    client = paho.Client(MQTT_CLIENT_NAME + "metrics_processing")

    cnt = 10
    while cnt > 0:
        try:
            client.connect(MQTT_HOST)
            break
        except Exception:
            logger.error("Cann not connetct to mqtt. %s", MQTT_HOST)
            cnt -= 1
            if cnt <= 0:
                raise

    humitidy_processing(client)


def humitidy_processing(client):
    gisteresis = 2
    humidity_limit = 50
    key = '370c3800'
    last_humidity = last_values.get("home/%s/dht_h" % key)
    last_temperature = last_values.get("home/%s/dht_t" % key)
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
                    namespace, wifipoint, name = key.split('/', 2)
                except ValueError:
                    print("error: %s" % key)
                    last_values.pop(key)
                    continue
                data.append(_metric('v', value, _time, **{
                    'point': wifipoint,
                    'name': name,
                }))
                last_values.pop(key)
        finally:
            _lock.release()

        resp.body = "\n".join(data) + "\n"



def process_metric():
    app = falcon.API()
    app.add_route('/metrics', ThingsResource())
    httpd = simple_server.make_server('127.0.0.1', 8000, app)
    httpd.serve_forever()


def process_mqtt_events():
    client = paho.Client(MQTT_CLIENT_NAME + "_subscribber")
    client.on_message = on_message
    cnt = 10
    while cnt > 0:
        try:
            client.connect(MQTT_HOST)
            break
        except Exception:
            logger.error("Cann not connetct to mqtt. %s", MQTT_HOST)
            cnt -= 1
            if cnt <= 0:
                raise
    client.subscribe(MQTT_SUBSRIBER_TOPIC)
    client.loop_start()

t = threading.Thread(target=process_metric)
t.setDaemon(True)
t.start()

t = threading.Thread(target=process_mqtt_events)
t.setDaemon(True)
t.start()

time.sleep(9999999999)
