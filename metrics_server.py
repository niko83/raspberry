from wsgiref import simple_server
import falcon
import time
import paho.mqtt.client as paho
import logging
import settings
import metrics_file
from locker import one_thread_restriction

logger = logging.getLogger("smarthome")


MQTT_CLIENT_NAME = 'raspberry_consumer_client'
MQTT_HOST = '127.0.0.1'

client = paho.Client(MQTT_CLIENT_NAME + "_metrics_worker")

while True:
    try:
        client.connect(MQTT_HOST)
        break
    except Exception as e:
        logger.error("Can not connect to mqtt %s", MQTT_HOST)
        time.sleep(5)


def processing(last_values):
    humitidy_processing(last_values)


def humitidy_processing(last_values):
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


def _metric(metric_name, val, _time, **labels):
    labels_str = ''
    if labels:
        labels_list = []
        for name, l_val in labels.items():
            labels_list.append('%s="%s"' % (name, l_val))
        labels_str = "{" + ','.join(labels_list) + "}"

    return "%s%s %s %s000" % (metric_name, labels_str, val, int(_time))


@one_thread_restriction(settings.LOCK_KEY)
def _process():
    last_values = metrics_file.read()

    processing(last_values)
    data = []
    for key, (value, _time) in last_values.items():

        try:
            namespace, wifipoint, name = key.split('/', 2)
        except ValueError:
            print("error: %s" % key)
            continue
        data.append(_metric('val', value, _time, **{
            'namespace': namespace,
            'wifipoint': wifipoint,
            'name': name,
        }))


    metrics_file.remove()
    return data


class ThingsResource(object):

    def on_get(self, req, resp):
        resp.body = "\n".join(_process())


app = falcon.API()
app.add_route('/metrics', ThingsResource())
httpd = simple_server.make_server('127.0.0.1', 8000, app)
httpd.serve_forever()
