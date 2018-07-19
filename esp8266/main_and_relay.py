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


last_conn = last_ping_client = time.time()

first_ping = []

def process(line):
    global last_ping_client
    if not line:
        if time.time() - last_ping_client > 2:
            beep('health_ping', period=60, freq=1000)
            if time.time() - last_ping_client > 200:
                raise HealthCheckError("Trere in't a ping from connected client.")
        return

    for cmd in line:
        if cmd == ord('0'):
            if not first_ping:
                first_ping.append(time.time())
            print(time.time() - first_ping[0], end=" ")
            last_ping_client = time.time()
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
        time.sleep(0.1)
        t = time.time()
        if http_server.has_connection():
            last_conn = t
        else:
            if t - last_conn > 5:
                beep("no_conn", period=30, freq=200)
                if t - last_conn > 300:
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
