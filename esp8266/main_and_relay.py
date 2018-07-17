import gc
import os
import socket
from time import sleep

import machine
import network
import websocket_helper
from websocket import websocket
from utils import PIN, beep
import time

#  machine.freq(160000000)
cnt = 0

beep(PIN.D8)


class HealthCheckError(Exception):
    pass

pins = {
    'D1': machine.Pin(PIN.D1, machine.Pin.OUT),
    'D2': machine.Pin(PIN.D2, machine.Pin.OUT),
}


for v in pins.values():
    v.on()  # Reverse relay


def send_file(filename, cl, gzip=False):
    start = 0
    slc = 3000

    print("Send file: %s" % filename)
    with open(filename, 'rb') as f:
        cnt_len = os.stat(filename)[6]
        cl.sendall('\n'.join([
            'HTTP/1.1 200 OK',
            'Connection: close',
            'Server: WebSocket Server',
            'Content-Length: {}'.format(cnt_len),
        ]))
        if gzip:
            cl.sendall('\ncontent-encoding: gzip\n\n')
        else:
            cl.sendall('\n\n')
        while True:
            f.seek(start)
            start += slc
            data = f.read(slc)
            if start % 500 == 0:
                print(".", end="")
            if data != b'':
                cl.sendall(data)
            else:
                break

    print("Send file finish: %s %s" % (filename, cnt_len))
    sleep(0.1)


class WebSocketClient:

    def __init__(self, s):
        self.socket = s
        self.last_ping = time.time()
        if not self.socket:
            return
        self.ws = websocket(self.socket, True)
        self.socket.setblocking(False)
        self.socket.setsockopt(socket.SOL_SOCKET, 20, None)

    def is_fake(self):
        return not bool(self.socket)

    def read(self):
        try:
            return self.ws.readline()
        except AttributeError:
            return

    def write(self, msg):
        try:
            self.ws.write(msg)
        except OSError:
            print("can not sent %s" % msg)

    def close(self):
        print("Closing connection.")
        if self.socket:
            self.socket.close()
            self.socket = None
            self.ws = None

    def process(self):
        line = self.read()
        if not line:
            if time.time() - self.last_ping > 5:
                raise HealthCheckError("Trere in't a ping from connected client.")
            return

        for cmd in line:
            if cmd == ord('0'):
                print("p", end="")
                self.last_ping = time.time()
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


class WebSocketServer:
    def __init__(self):
        self._listen_s = None
        self._ws_client = WebSocketClient(None)  # fake client
        port = 80
        self._listen_s = socket.socket()
        self._listen_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listen_s.bind(socket.getaddrinfo('0.0.0.0', port)[0][-1])
        self._listen_s.listen(1)
        self._listen_s.setsockopt(socket.SOL_SOCKET, 20, self._accept_conn)
        for i in (network.AP_IF, network.STA_IF):
            iface = network.WLAN(i)
            if iface.active():
                print("WebSocket started on ws://%s:%d" % (iface.ifconfig()[0], port))

    def _accept_conn(self, listen_sock):
        cl, remote_addr = listen_sock.accept()
        print("Client connection from:", remote_addr, end=" ")

        cl_file = cl.makefile('rwb', 0)
        path = cl_file.readline()
        print(path)

        ws = False
        if path.startswith(b'GET /ws/'):
            ws = True

        if not ws:
            while True:
                line = cl_file.readline()
                if not line or line == b'\r\n':
                    break

            try:
                if 'jquery.js' in path:
                    send_file('jquery.js.gz', cl, True)
                elif '/favicon.ico' in path:
                    send_file('favicon.ico', cl)
                else:
                    send_file('index.html.gz', cl, True)
            except OSError as e:
                print("%s %s" % (e, path))

            cl.close()
            return

        try:
            websocket_helper.server_handshake(cl)
        except OSError:
            cl.setblocking(True)
            cl.sendall("HTTP/1.1 503 ws error\n\n")
            cl.sendall("\n")
            # TODO: Make sure the data is sent before closing
            sleep(0.1)
            cl.close()
            return

        self._ws_client.close()
        self._ws_client = WebSocketClient(cl)

    def stop(self):
        if self._listen_s:
            self._listen_s.close()
        self._listen_s = None
        self._ws_client.close()
        print("Stopped WebSocket server.")


try:
    server = WebSocketServer()
except Exception as e:
    print("Unknown Error while start websocket %s %s" % (type(e), e))
    machine.reset()

start_time = time.time()
#  last_diff_p = _last_diff = 0
last_ping = time.time()
try:
    while True:
        if server._ws_client.is_fake():
            if time.time() - last_ping > 20:
                raise HealthCheckError("Trere aren't any connections.")
            continue
        else:
            last_ping = time.time()

        cnt += 1
        if time.time() != start_time:
            start_time = time.time()
            cnt = 0
        try:
            server._ws_client.process()
        except HealthCheckError:
            raise
        except Exception as e:
            print("Recreate server. %s %s" % (type(e), e))
            server.stop()
            server = WebSocketServer()
except Exception as e:
    print("%s %s" % (type(e), e))
    machine.reset()
