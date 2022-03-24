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

def startDump(net:net, hosts):
    hostnum = 1
    for host in hosts:
        host.cmd('tcpdump -w '+pcapPath+'h'+str(hostnum)+'.pcap&')
        print("starting tcpdump on host: ", host)
        time.sleep(1)
        hostnum += 1


def startClients(net:net, clients):
    logfile = open(pcapPath + 'sendParams.csv', 'w')
    writer = csv.writer(logfile)
    header = ['host', 'serverIP', 'port', 'duration', 'size', 'proto']
    writer.writerow(header)

    # generate random ports
    ports = random.sample(range(10000, 2**16-1), len(clients))

    # generate random application

    # start ITGSend on clients
    for i in range(len(clients)):
        # generate random duration 
        dur = random.randint(1000, 20*1000)
        app = ''
        if random.randint(0, 1):
            app = 'Telnet'
        
        print("starting ITGSend on host: ", clients[i])
        print(clients[i].cmd('ITGSend -a ' + serverIP +' -rp '+ str(ports[i]) +' -C ' + str(dur) + ' -c 512 -T TCP ' + app + ' &'))
        writer.writerow([clients[i], serverIP, str(ports[i]), str(dur), '512', 'TCP ' + app])
    
    logfile.close()

def Test(net:net):
    numHosts = len(net.hosts)
    
    hosts = []
    for i in range(1, numHosts + 1):
        hosts.append(net.get('h'+str(i)))

    serv = hosts[0]
    clients = hosts[1:]
    
    # run tcpdump on each node
    startDump(net, hosts)
    
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
        
        # set locations for appropriate run
        global pcapPath
        runId = os.popen('cat tempFiles/runId.txt').read()
        runId = int(runId)
        pcapPath = pcapPath + str(runId) + '/'
        os.system('mkdir -p ' + pcapPath)


        #initialize parmeters here
        numHosts = os.popen('cat tempFiles/numHost.txt').read()
        numHosts = int(numHosts)
        numClients = numHosts - 1

        # open log file
        logfile = open(pcapPath + 'topo.csv', 'w')
        writer = csv.writer(logfile)
        header = [ 'host', 'IP' ]
        writer.writerow(header)

        # creating topology
        hosts = []
        #  add server
        hosts.append(self.addHost('h1', ip=serverIP + '/' + str(serverMask)))
        writer.writerow([ 'h1', serverIP + '/' + str(serverMask)])

        # clients
        clients = []

        if not os.path.exists('./tempFiles/IpAdresses.txt'):
            os.system('./generateIPs.py')
        
        ipFile = open('./tempFiles/IpAdresses.txt', 'r')
        clientIPs = ipFile.read().splitlines()

        ipIndices = random.sample(range(0, len(clientIPs)), numClients)

        for i in range(0, numClients):
            clients.append(self.addHost('h'+str(i+2), ip=clientIPs[ipIndices[i]]))
            writer.writerow(['h'+str(i+2), clientIPs[ipIndices[i]]])

        s1=self.addSwitch('s1')

        hosts = hosts + clients

        # join hosts with switch
        for h in hosts:
            self.addLink(h,s1, bw=10, delay='2ms')

        logfile.close()

topos={'mytopo':(lambda:MyTopo())}      



    
