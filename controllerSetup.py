#!/usr/bin/python                                                                                      
                                                                                                       
from time import sleep
from mininet.net import Mininet                                                                        
from mininet.node import Controller
from mininet.node import RemoteController                                                                   
from mininet.topo import SingleSwitchTopo                                                             
from mininet.log import setLogLevel                                                                    
                                                                                                       
import os                                                                                              
                                                                                                    
class POXBridge( Controller ):                                                                         
    "Custom Controller class to invoke POX forwarding.l2_learning"                                     
    def start( self ):                                                                                 
        "Start POX learning switch"                                                        
        self.pox = './pox.py'                                            
        self.cmd( self.pox, 'log.level --DEBUG l2_learning_mod flow_info_extractor --filename=test1.txt &' )                                               
    def stop( self ):                                                                                  
        "Stop POX"                                                                                     
        self.cmd( 'kill %' + self.pox )                                                                
                                                                                                       
controllers = { 'poxbridge': POXBridge }                                                               
                                                                                                       
if __name__ == '__main__':                                                                             
    setLogLevel( 'info' )                                                                          
    net = Mininet( topo=SingleSwitchTopo( 2 ),)
    net.addController( 'c0', controller=RemoteController, ip='127.0.0.1', port=6633 )                                
    net.start()                                                                                        
    net.pingAll()
    h1 = net.get('h1')
    print(h1.cmd('ip addr'))
    sleep(10)                                                                                     
    net.stop()      
