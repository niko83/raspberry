import machine
from utils import PIN, beep, http_server
import time


class HealthCheckError(Exception):
    pass

#  machine.freq(160000000)

beep("start", period=300, freq=8000)

pins = {
    'D1': machine.Pin(PIN.D1, machine.Pin.OUT),
    'D2': machine.Pin(PIN.D2, machine.Pin.OUT),
}

for v in pins.values():
    v.on()  # Reverse relay


last_conn = time.time()
last_ping_client = 999999

first_ping = []


def process(line):
    global last_ping_client
    t = time.time()
    if not line:
        if t - last_ping_client > 1:
            beep('health_ping', period=40, freq=1000)
            if t - last_ping_client > 15:
                raise HealthCheckError("Trere in't a ping from connected client.")
        return

    for cmd in line:
        if cmd == ord('0'):
            if not first_ping:
                first_ping.append(t)
            if last_ping_client  != t:
                print(t - first_ping[0], end=" ")
            last_ping_client = t
        elif cmd == ord('1'):
            pins['D1'].off()
        elif cmd == ord('2'):
            pins['D1'].on()
        elif cmd == ord('3'):
            pins['D2'].off()
        elif cmd == ord('4'):
            pins['D2'].on()
        else:
            print("Unknown CMD: %s (%s)" % (cmd, line.decode('utf8')))

try:
    while True:
        time.sleep(0.005)
        t = time.time()
        if http_server.has_connection():
            last_conn = t
        else:
            if t - last_conn > 5:
                beep("no_conn", period=20, freq=100)
                if t - last_conn > 120:
                    raise HealthCheckError("Trere aren't any connections.")
                continue

        try:
            process(http_server.read())
        except HealthCheckError:
            raise
        #  except Exception as e:
            #  machine.reset()
            #  http_server.restart(e)
except Exception as e:
    print("%s %s" % (type(e), e))
    machine.reset()
