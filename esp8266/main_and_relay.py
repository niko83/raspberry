import time
import socket
import machine
import network

import gc
print("Free mem: %s" % gc.mem_free())


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

pins = {
    'D1': machine.Pin(PIN.D1, machine.Pin.OUT),
    'D2': machine.Pin(PIN.D2, machine.Pin.OUT),
    #  'D3': machine.Pin(PIN.D3, machine.Pin.OUT),
    #  'D4': machine.Pin(PIN.D4, machine.Pin.OUT),
}
for v in pins.values():
    v.on()

wlan = network.WLAN(network.AP_IF)
wlan.config(essid="", password="")
wlan.ifconfig(('192.168.0.10', '255.255.255.0', '192.168.0.1', '8.8.8.8'))
wlan.active(True)
print(wlan.ifconfig())
print("==========")

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print('listening on', addr)


def send_file(filename, cl, gzip=False):
    start = 0
    slc = 2
    with open(filename, 'rb') as f:
        if gzip:
            cl.send('\n'.join([
                'HTTP/1.1 200 OK',
                #  'Cache-Control: max-age=3600, must-revalidate',
                'content-encoding: gzip\n\n'
            ]))
        while True:
            f.seek(start)
            start += slc
            data = f.read(slc)
            print(start)
            if data != b'':
                cl.send(data)
            else:
                break

try:
    while True:
        cl, addr = s.accept()
        print('client connected from', addr)
        cl_file = cl.makefile('rwb', 0)
        cmd = ["", ""]
        while True:
            line = cl_file.readline()
            if line.startswith(b'GET '):
                cmd = line.decode("utf8").split("/")[1:]
            if not line or line == b'\r\n':
                break
        print(cmd)

        if cmd[0] == 'test':
            for v in sorted(pins.keys()):
                pins[v].off()
                time.sleep(0.4)
                pins[v].on()
                time.sleep(0.4)
        elif cmd[0] == 'jquery.js HTTP':
            send_file('jquery.js.gz', cl, True)
        elif cmd[0] in pins.keys():
            if cmd[1] == '1':
                pins[cmd[0]].off()
            else:
                pins[cmd[0]].on()
        else:
            send_file('index.html', cl)

        cl.close()
except Exception as e:
    print("Unknown Error %s" % e)
    machine.reset()
