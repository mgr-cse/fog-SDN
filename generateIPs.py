#!/usr/bin/python3

import random
import socket
import struct

classA = range(167772160 + 2, 184549375 + 1)    # exclude the server
classB = range(2886729728, 2887778303 + 1)
classC = range(3232235520, 3232301055 + 1)

sampleA = random.sample(classA, 30)
#sampleB = random.sample(classB, 15)

ipFile = open('IpAdresses.txt', 'w')

for s in sampleA:
    ipString = socket.inet_ntoa(struct.pack('>I', s)) + '/8'
    ipFile.write(ipString + '\n')

'''
for s in sampleB:
    ipString = socket.inet_ntoa(struct.pack('>I', s)) + '/16'
    ipFile.write(ipString + '\n')
'''

ipFile.close()


