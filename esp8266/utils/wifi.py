import machine
import network
from lib import logging
import time
log = logging.getLogger(__name__)

network.WLAN(network.AP_IF).active(False)

_auto_connection_recheck = 120000


def check_connection():
    if network.WLAN(network.STA_IF).isconnected():
        log.info('WiFi connection OK.')
    else:
        log.warning('WiFi connection failed. RESET.')
        machine.reset()


def do_connect(ssid, password, ip=None, timeout=10000):

    tim = machine.Timer(-1)
    tim.init(
        period=timeout,
        mode=machine.Timer.ONE_SHOT,
        callback=lambda t: check_connection(),
    )

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if ip:
        wlan.ifconfig(ip)
    wlan.connect(ssid, password)

    log.info('Connecting to network...')
    while True:
        if not wlan.isconnected():
            time.sleep(0.2)
        else:
            log.info('Successfully Connected to network: %s', wlan.ifconfig())
            tim.init(
                period=_auto_connection_recheck,
                mode=machine.Timer.PERIODIC,
                callback=lambda t: check_connection(),
            )
            return
