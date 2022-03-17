from http import client
import random
import time
import os
import csv

from mininet import net
from mininet.topo import Topo
from mininet.node import Node

pcapPath = './pcaps/'
logPath = './testLogs/'
serverIP = '10.0.0.1'
serverMask = 8
run =  1

dataPath = './pox-runs/run'+str(run)+'/'

def startDump(net:net, hosts):
    hostnum = 1
    for host in hosts:
        host.cmd('tcpdump -w '+pcapPath+'h'+str(hostnum)+'.pcap&')
        print("starting tcpdump on host: ", host)
        time.sleep(1)
        hostnum += 1


def startClients(net:net, clients):
    hostIndex = 2
    for client in clients:
        interface = 'h' + str(hostIndex) + '-eth0'
        print(client.cmd('tcpreplay -i ' + interface + ' ' + dataPath + 'h' + str(hostIndex) + '.pcap &'))
        hostIndex += 1
    
def Test(net:net):
    numHosts = len(net.hosts)
    
    hosts = []
    for i in range(1, numHosts + 1):
        hosts.append(net.get('h'+str(i)))

    serv = hosts[0]
    clients = hosts[1:]
    
    # run tcpdump on each node
    #startDump(net, hosts)
    
    time.sleep(2)

    # start server application
    print(serv.cmd('ITGRecv &'))

    time.sleep(2)
    
    # client
    startClients(net, clients)

    time.sleep(60)


tests = { 'test': Test }

# creating topology with custom IPs
class MyTopo(Topo):
    def __init__(self):
        #initialize topology
        Topo.__init__(self)

        #initialize parmeters here
        numHosts = 10
        numClients = numHosts - 1


        # creating topology
        hosts = []
        #  add server
        hosts.append(self.addHost('h1', ip=serverIP + '/' + str(serverMask)))

        # clients
        clients = []

        if not os.path.exists('./IpAdresses.txt'):
            os.system('./generateIPs.py')

        clientIPs = []
        
        ipFile = open(dataPath+'topo.csv', 'r')
        csvReader = csv.reader(ipFile)
        next(csvReader)
        next(csvReader)
        for row in csvReader:
            clientIPs.append(row[1])

        for i in range(0, numClients):
            clients.append(self.addHost('h'+str(i+2), ip=clientIPs[i]))


        s1=self.addSwitch('s1')

        hosts = hosts + clients

        # join hosts with switch
        for h in hosts:
            self.addLink(h,s1, bw=10, delay='2ms')

topos={'mytopo':(lambda:MyTopo())}      
