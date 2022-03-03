import random
import time

from mininet import net

pcapPath = './pcaps/'

def startDump(net:net, hosts):
    hostnum = 1
    for host in hosts:
        host.cmd('tcpdump -w '+pcapPath+'h'+str(hostnum)+'.pcap&')
        print("starting tcpdump on host: ", host)
        time.sleep(1)
        hostnum += 1


def startClients(net:net, clients):
    # generate random ports
    ports = random.sample(range(10000, 2**16-1), len(clients))

    # start ITGSend on clients
    for i in range(len(clients)):
        print("starting ITGSend on host: ", clients[i])
        print(clients[i].cmd('ITGSend -a 10.0.0.1 -rp '+str(ports[i])+' -C 1000 -c 512 -T TCP &'))

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

    time.sleep(1000)


tests = { 'test': Test }


    
