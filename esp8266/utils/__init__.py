import network
import time
import gc
import machine

from utils.settings import Settings
import ubinascii
from umqtt.simple import MQTTClient


def mqtt_val(val):
    return bytes(str(val), 'utf-8')

rtc = machine.RTC()
rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)


def deepsleep():
    time.sleep_ms(300)
    rtc.alarm(rtc.ALARM0, deepsleep_interval)
    print("machine is going to deeplseep")
    machine.deepsleep()


pwm = None
beeps = {}


class PIN:
    D0 = 16  # build-in led
    D1 = 5
    D2 = 4
    D3 = 0
    D4 = 2
    D5 = 14
    D6 = 12
    D7 = 13
    D8 = 15
    D9 = 3
    D10 = 1
    map_to_d = {
        16: 'D0',
        5: 'D1',
        4: 'D2',
        0: 'D3',
        2: 'D4',
        14: 'D5',
        12: 'D6',
        13: 'D7',
        15: 'D8',
        3: 'D9',
        1: 'D10',
    }
    str_to_pin = dict((v, k) for k, v in map_to_d.items())


for p in PIN.map_to_d.keys():
    machine.Pin(PIN.D8, machine.Pin.OUT).off()

client_id = ubinascii.hexlify(machine.unique_id()).decode("utf-8")
print("Client_id: %s" % client_id)


def beep(key, pin=PIN.D8, period=200, freq=410, limit=True):
    global pwm
    t = time.time()
    if key not in beeps:
        beeps[key] = t

    if beeps[key] != t or limit is False:
        print("%s(%.1f)" % (key, gc.mem_free()/1024.0), end=" ")
        beeps[key] = t
        pwm = machine.PWM(machine.Pin(pin), freq=freq, duty=500)
        machine.Timer(-1).init(
            period=period,
            mode=machine.Timer.ONE_SHOT,
            callback=lambda x: pwm.deinit()
        )

beep("start", period=100, freq=600, limit=False)
time.sleep(0.10)


if Settings.WIFI_AP_ENABLED:
    print("WiFi as AP")
    wlan = network.WLAN(network.AP_IF)
    try:
        wlan.active(True)
    except OSError:
        machine.reset()
    wlan.config(essid=Settings.WIFI_AP[0], password=Settings.WIFI_AP[1])
    wlan.ifconfig(('192.168.0.10', '255.255.255.0', '192.168.0.1', '8.8.8.8'))
    print("WLAN config: %s" % repr(wlan.ifconfig()))
else:
    network.WLAN(network.AP_IF).active(False)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    all_wifi = tuple(w[0].decode("utf8") for w in wlan.scan())
    for wifi_name, wifi_pass in Settings.WIFI:
        if wifi_name not in all_wifi:
            print("WLAN skipped %s" % wifi_name)
            continue
        print("WLAN connect %s:%s" % (wifi_name, wifi_pass))
        wlan.connect(wifi_name, wifi_pass)
        c = 0
        while c < 10:
            beep("wifi_conn", period=5, freq=1000, limit=False)
            if wlan.isconnected():
                break
            c += 1
            time.sleep(1)
            print("WLAN attemp: %s" % c)

        if wlan.isconnected():
            break

    if wlan.isconnected():
        print("WLAN config: %s" % repr(wlan.ifconfig()))
    else:
        print("WLAN in not connected. Bye, bye..")
        machine.reset()

    if Settings.MQTT_IP:
        c = 0
        while True:
            try:
                beep("wifi_conn", period=5, freq=800, limit=False)
                print("MQTT: try connect %s, attemp %s" % (Settings.MQTT_IP, c))
                client = MQTTClient(client_id, Settings.MQTT_IP)
                client.connect()
                break
            except:
                time.sleep(1)
                c += 1
                if c > 30:
                    machine.reset()
        print("MQTT: Successfully connected")

_last_mqtt_heartbit = time.time()


def check_heartbit(topic):
    global _last_mqtt_heartbit
    topic = topic.decode('utf-8')
    topic = topic.split('/')[-1]
    if topic == "heartbit":
        _last_mqtt_heartbit = time.time()

    if time.time() - _last_mqtt_heartbit > 300:
        return 'ERROR'
