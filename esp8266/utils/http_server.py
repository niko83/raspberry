import socket
import time
import os
import machine
from websocket import websocket

import websocket_helper


_client = None
_listen_s = None
_ws = None


def _send_file(filename, cl, gzip=False):
    start = 0
    slc = 500

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
    time.sleep(0.1)


def _accept_conn(listen_sock):
    global _client
    global _ws

    cl, remote_addr = listen_sock.accept()
    print("Client connection from: %s" % str(remote_addr), end=" ")

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
                _send_file('jquery.js.gz', cl, True)
            elif '/favicon.ico' in path:
                _send_file('favicon.ico', cl)
            else:
                _send_file('index.html.gz', cl, True)
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
        time.sleep(0.1)
        cl.close()
        return

    if _client:
        _destroy_client()

    _client = cl
    _ws = websocket(_client, True)
    _client.setblocking(False)
    _client.setsockopt(socket.SOL_SOCKET, 20, None)


listen_s = socket.socket()
listen_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listen_s.bind(socket.getaddrinfo('0.0.0.0', 80)[0][-1])
try:
    listen_s.listen(1)
except OSError as e:
    print("RESET %s %s" % (type(e), e))
    machine.reset()
listen_s.setsockopt(socket.SOL_SOCKET, 20, _accept_conn)
print("WebSocketServer START.")


def _destroy_client():
    global _client
    global _ws
    _client.close()
    _client = None
    _ws = None


def has_connection():
    return bool(_client)


def restart(e):
    global _listen_s

    if _listen_s:
        _listen_s.close()
    _listen_s = None
    _destroy_client()

    print("WebSocketServer RECREATE. %s %s" % (type(e), e))


def read():
    try:
        return _ws.readline()
    except AttributeError:
        return None
