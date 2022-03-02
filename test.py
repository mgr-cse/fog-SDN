import os
import sys
import time

from mininet import net

pcapPath = './pcaps/'

def setClients(net:net, clients):
    hostnum = 1
    for host in clients:
        host.cmd('tcpdump -w '+pcapPath+'h'+str(hostnum)+'.pcap&')
        print("starting tcpdump on host: ", host)
        time.sleep(1)
        hostnum += 1

def Test(net:net):
    numHosts = len(net.hosts)
    
    hosts = []
    for i in range(1, numHosts + 1):
        hosts.append(net.get('h'+str(i)))
    
    # run tcpdump on each node
    setClients(net, hosts)
    
    # each client pings server h1
    for i in range(1, numHosts):
        hosts[i].cmd('ping -c 1 10.0.0.1')

    time.sleep(2)

    # start server application
    print(hosts[0].cmd('ITGRecv &'))

    time.sleep(2)
    
    # start client application
    #for i in range(1, numHosts):
    print(hosts[1].cmd('ITGSend ./itg.sh'))

    time.sleep(5)


tests = { 'test': Test }


    
