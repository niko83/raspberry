import gc
import os
import socket
from time import sleep

import machine
import network
import websocket_helper
from websocket import websocket
from utils import PIN

#  machine.freq(160000000)

pins = {
    'D1': machine.Pin(PIN.D1, machine.Pin.OUT),
    'D2': machine.Pin(PIN.D2, machine.Pin.OUT),
    #  'D3': machine.Pin(PIN.D3, machine.Pin.OUT),
    #  'D4': machine.Pin(PIN.D4, machine.Pin.OUT),
}

# Reverse relay
for v in pins.values():
    v.on()


def send_file(filename, cl, gzip=False):
    start = 0
    slc = 2000

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
            if start % 1000 == 0:
                print("%s %.1f" % (filename, (100 * start/cnt_len)), end=" ")
            if data != b'':
                cl.sendall(data)
            else:
                print("%s finish" % filename)
                break

    sleep(0.1)


class WebSocketConnection:
    def __init__(self, addr, s, close_callback):
        self.address = addr
        self.socket = s
        self.close_callback = close_callback

        self.ws = websocket(self.socket, True)
        self.client_close = False
        self._need_check = False
        s.setblocking(False)
        s.setsockopt(socket.SOL_SOCKET, 20, self.notify)

    def notify(self, s):
        self._need_check = True

    def read(self):
        if self._need_check:
            self._check_socket_state()

        msg_bytes = None
        try:
            msg_bytes = self.ws.readline()
        except OSError:
            self.client_close = True

        if not msg_bytes and self.client_close:
            self.close_callback(self)
            return

        return msg_bytes

    def write(self, msg):
        try:
            self.ws.write(msg)
        except OSError:
            self.client_close = True

    def _check_socket_state(self):
        self._need_check = False
        sock_str = str(self.socket)
        state_str = sock_str.split(" ")[1]
        state = int(state_str.split("=")[1])

        if state == 3:
            self.client_close = True

    def is_closed(self):
        return self.socket is None

    def close(self):
        print("Closing connection.")
        self.socket.setsockopt(socket.SOL_SOCKET, 20, None)
        self.socket.close()
        self.socket = None
        self.ws = None
        if self.close_callback:
            self.close_callback(self)


class WebSocketClient:
    def __init__(self, conn):
        self.connection = conn

    def process(self):
        line = self.connection.read()
        if not line:
            return

        cmd = line.decode("utf8").strip("/").split("/")
        while True:
            try:
                pin = cmd.pop(0)
                act = cmd.pop(0)
            except IndexError:
                break

            if pin in pins.keys():
                if act == '1':
                    if pins[pin].value() == 1:
                        pins[pin].off()
                else:
                    if pins[pin].value() == 0:
                        pins[pin].on()


class WebSocketServer:
    def __init__(self):
        self._listen_s = None
        self._clients = []
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
        print("Client connection from:", remote_addr)

        if len(self._clients) >= 10:
            print("Too many connections.")
            cl.setblocking(True)
            cl.sendall("HTTP/1.1 503 Too many connections\n\n")
            cl.sendall("\n")
            # TODO: Make sure the data is sent before closing
            sleep(0.1)
            cl.close()
            return

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
                    send_file('index.html', cl)
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
        self._clients.append(
            WebSocketClient(WebSocketConnection(remote_addr, cl, self.remove_connection))
        )

    def stop(self):
        if self._listen_s:
            self._listen_s.close()
        self._listen_s = None
        for client in self._clients:
            client.connection.close()
        print("Stopped WebSocket server.")

    def process_all(self):
        for client in self._clients:
            client.process()

    def remove_connection(self, conn):
        for client in self._clients:
            if client.connection is conn:
                self._clients.remove(client)

server = WebSocketServer()
print("Free mem: %s" % gc.mem_free())
try:
    while True:
        server.process_all()
except Exception as e:
    print("Unknown Error %s" % e)
    machine.reset()
