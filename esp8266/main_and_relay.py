import gc
import os
import socket
from time import sleep

import machine
import network
import websocket_helper
from websocket import websocket


machine.freq(160000000)

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


if True:
    from utils import wlan
else:
    wlan = network.WLAN(network.AP_IF)
    wlan.config(essid="", password="")
    wlan.ifconfig(('192.168.0.10', '255.255.255.0', '192.168.0.1', '8.8.8.8'))
    wlan.active(True)
    print(wlan.ifconfig())
    print("==========")


def send_file(filename, cl, gzip=False):
    start = 0
    slc = 2
    with open(filename, 'rb') as f:
        if gzip:
            cl.send('\n'.join([
                'HTTP/1.1 200 OK',
                'Content-Length: {}'.format(os.stat(filename)[6]),
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

    sleep(0.1)
    cl.close()

#  try:
#  print(machine.disable_irq())


class ClientClosedError(Exception):
    pass


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
            raise ClientClosedError()

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

        cmd = line.decode("utf8").split("/")
        print(cmd)
        if cmd[0] in pins.keys():
            if cmd[1] == '1':
                if pins[cmd[0]].value() == 1:
                    pins[cmd[0]].off()
            else:
                if pins[cmd[0]].value() == 0:
                    pins[cmd[0]].on()


class WebSocketServer:
    def __init__(self, page):
        self._listen_s = None
        self._clients = []
        self._page = page

    def start(self, port=80):
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

        #  if len(self._clients) >= self._max_connections:
            #  # Maximum connections limit reached
            #  cl.setblocking(True)
            #  cl.sendall("HTTP/1.1 503 Too many connections\n\n")
            #  cl.sendall("\n")
            #  # TODO: Make sure the data is sent before closing
            #  sleep(0.1)
            #  cl.close()
            #  return

        cl_file = cl.makefile('rwb', 0)
        line = cl_file.readline()
        print(line)

        ws = False
        if line.startswith(b'GET /ws/'):
            ws = True
        else:
            cmd = line.decode("utf8").split("/")[1:]
            print(cmd)

        if not ws:

            while True:
                line = cl_file.readline()
                if not line or line == b'\r\n':
                    break

            if cmd[0] == 'jquery.js HTTP':
                send_file('jquery.js.gz', cl, True)
            elif cmd[0] == ' HTTP':
                send_file('index.html', cl)
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


    #  def _serve_page(self, sock):
        #  try:
            #  sock.sendall('HTTP/1.1 200 OK\nConnection: close\nServer: WebSocket Server\nContent-Type: text/html\n')
            #  length = os.stat(self._page)[6]
            #  sock.sendall('Content-Length: {}\n\n'.format(length))
            #  # Process page by lines to avoid large strings
            #  with open(self._page, 'r') as f:
                #  for line in f:
                    #  sock.sendall(line)
        #  except OSError:
            #  pass
        #  sock.close()

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
        return

asd = WebSocketServer("/index.html")
asd.start()
while True:
    asd.process_all()
#  ###########################
#
#  gc.collect()
#  while True:
#      print('client connected from', addr)
#      print("1 %s" % time.time())
#      cl, _ = s.accept()
#      print("2 %s" % time.time())
#      cl_file = cl.makefile('rwb', 0)
#      print("3 %s" % time.time())
#      cmd = ["", ""]
#      while True:
#          line = cl_file.readline()
#          if line.startswith(b'GET '):
#              cmd = line.decode("utf8").split("/")[1:]
#          if not line or line == b'\r\n':
#              break
#
#      print("4")
#
#      if cmd[0] in pins.keys():
#          if cmd[1] == '1':
#              if pins[cmd[0]].value() == 1:
#                  pins[cmd[0]].off()
#          else:
#              if pins[cmd[0]].value() == 0:
#                  pins[cmd[0]].on()
#
#          print("5")
#      elif cmd[0] == 'test':
#          for v in sorted(pins.keys()):
#              pins[v].off()
#              time.sleep(0.4)
#              pins[v].on()
#              time.sleep(0.4)
#      elif cmd[0] == 'jquery.js HTTP':
#          send_file('jquery.js.gz', cl, True)
#      elif cmd[0] == ' HTTP':
#          send_file('index.html', cl)
#      cl.close()
#      print("6")
#
#  except Exception as e:
#      print("Unknown Error %s" % e)
#      machine.reset()
