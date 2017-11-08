import machine
import network
from lib import logging
import time
from utils.settings import Config
log = logging.getLogger(__name__)

network.WLAN(network.AP_IF).active(False)

_auto_connection_recheck = 120000


def disconnect():
    network.WLAN(network.STA_IF).disconnect()

def check_connection():
    counter = 60
    while counter > 0:
        if network.WLAN(network.STA_IF).isconnected():
            log.info('WiFi connection OK.')
            return
        counter -= 1
        time.sleep(0.5)
    log.warning('WiFi connection failed. RESET.')
    machine.reset()


def do_connect(timeout=10000):

    tim = machine.Timer(-1)
    tim.init(
        period=timeout,
        mode=machine.Timer.ONE_SHOT,
        callback=lambda t: check_connection(),
    )

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if Config.IP:
        wlan.ifconfig(Config.IP)
    wlan.connect(Config.WIFI_SSID, Config.WIFI_PASS)

    log.info('Connecting to network...')
    while True:
        if wlan.isconnected():
            return
        time.sleep(0.2)
        #  else:
            #  log.info('Successfully Connected to network: %s', wlan.ifconfig())
            #  tim.init(
                #  period=_auto_connection_recheck,
                #  mode=machine.Timer.PERIODIC,
                #  callback=lambda t: check_connection(),
            #  )
            #  return
