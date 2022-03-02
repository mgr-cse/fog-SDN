#!/bin/python

import sys
import socket

numClients = int(sys.argv[1])
basePort = 10000

host = ''
socks = []
conns = []
addrs = []

for i in range(numClients):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(host, basePort + i + 1)
    s.listen(1)
    conn, addr = s.accept()
    socks.append(s)
    conns.append(conn)
    addrs.append(addr)

while True:
    for conn in conns:
        try:
            data = conn.recv(1024)
            if not data: break
        except socket.error:
            break

