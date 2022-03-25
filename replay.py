from http import client
import random
import time
import os
import csv

from mininet import net
from mininet.topo import Topo
from mininet.node import Node

serverIP = '10.0.0.1'
serverMask = 8

dataPath = ''


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

        # number of hosts
        numHosts = os.popen('cat tempFiles/numHost.txt').read()
        numHosts = int(numHosts)
        numClients = numHosts - 1

        # get runId
        runId = os.popen('cat tempFiles/runId.txt').read()
        runId = int(runId)

        global dataPath
        dataPath = './pox-data/' + str(numHosts) + '/pcaps/' + str(runId) + '/'


        # creating topology
        hosts = []
        #  add server
        hosts.append(self.addHost('h1', ip=serverIP + '/' + str(serverMask)))

        # clients
        clients = []

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
