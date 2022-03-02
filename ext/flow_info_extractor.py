from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
from pox.openflow.of_json import flow_stats_to_list
import pox.lib.packet as pkt

from time import time
import csv
import socket
import json
import os
import copy
import pickle
import sklearn

## GLOBAL VARS
# learning rates
gamma_iat = 0.7
gamma_rtt = 0.7
# sampling period
T = 1
# pox logger
log = core.getLogger()

# dict to store data about unique flows 
flows = {}      # current stats about flows
history = {}    # stats about flow in previous sampling time
# header for csv with flow data stored
header = ['time', 'source.IP', 'dest.IP', 'source.port', 'dest.port', 'nw_proto', 'fwd.total_packets', 'fwd.total_bytes', 'bwd.total_packets', 'bwd.total_bytes', 'duration', 'iat_est', 'rtt_est']


# def send_data(sock, data_list):
#     data = str(data_list).encode('utf-8')
#     sock.send(data)


## TIMER MODULE FUNCTION
# timer function that invokes write-out periodically
def _timer_func (writer, sock, loaded_model):
    for connection in core.openflow._connections.values():
        connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))
        # connection.send(of.ofp_stats_request(body=of.ofp_port_stats_request()))
        log.debug("Sent flow stats request to %s", dpid_to_str(connection.dpid))
        log.debug("updating flow stats in file...")
        now = time()
        for key, f in flows.items():
            l = f.to_list(now)
            writer.writerow(l)
            flows[key].update_rtt_iat(key)                  # update iat & rtt every sampling time
            history[key] = copy.deepcopy(flows[key])        # store current state in history
            # send_data(sock, json.dumps(f.to_list()))
            if loaded_model is not None:
                pred = loaded_model.predict(l[1:])




## FLOW CLASS
class Flow:
    def __init__ (self, nw_src, nw_dst, tp_src, tp_dst, dpid, nw_proto, dl_type, packets=0, bytes=0):
        # attributes that uniquely identify a flow
        self.start_time = time()
        self.nw_src = nw_src
        self.nw_dst = nw_dst
        self.tp_src = tp_src
        self.tp_dst = tp_dst
        self.dpid = dpid
        self.nw_proto = nw_proto
        self.dl_type = dl_type

        # attributes that are collected over time
        self.fwd_packets = packets
        self.fwd_bytes = bytes
        self.bwd_packets = 0
        self.bwd_bytes = 0
        self.duration = 0.00

        # iat & rtt for further estimates
        self.iat = 0.00
        self.rtt = 0.00

    def update_forward (self, packets, bytes, duration):
        # curr_time = time()
        self.fwd_packets = packets
        self.fwd_bytes = bytes
        self.duration = duration
        # self.duration = time() - self.start_time

    def update_reverse (self, packets, bytes, duration):
        # curr_time = time()
        self.bwd_packets = packets
        self.bwd_bytes = bytes
        self.duration = duration
        # self.duration = time() - self.start_time

    def update_rtt_iat (self, key):
        # sampled info
        del_f = self.fwd_packets - history[key].fwd_packets
        del_b = self.bwd_packets - history[key].bwd_packets
        d = self.duration - history[key].duration
            
        # debug info
        self.print_flow()
        history[key].print_flow()
        print("d = %f, del_f = %f, del_b = %f"%(d,del_f, del_b))
            
        # update rtt
        if del_f == 0 and del_b == 0:
          pass
        if del_f > del_b and del_f != 0:
           self.rtt = gamma_rtt*self.rtt + (1-gamma_rtt)*(del_b/del_f + (del_f - del_b)*2*d)/del_f
        elif del_b > del_f and del_b != 0:
           self.rtt = gamma_rtt*self.rtt + (1-gamma_rtt)*(del_f*d + (del_b - del_f)*2*d)/del_b
        else:
           pass
            
        # update iat
        # if both directed flows are giving differences, take avg
        if del_f != 0 and del_b != 0:
            self.iat = gamma_iat*self.iat + (1-gamma_iat)*(d/del_f + d/del_b)/2
        # else take the non zero one
        elif del_f != 0:
            self.iat = gamma_iat*self.iat + (1-gamma_iat)*(d/del_f)
        elif del_b != 0:
            self.iat = gamma_iat*self.iat + (1-gamma_iat)*(d/del_b)
        # else don't update
        else:
            pass




    def to_list (self, time):
        return [time, self.nw_src, self.nw_dst, self.tp_src, self.tp_dst, self.nw_proto,
            self.fwd_packets, self.fwd_bytes, self.bwd_packets,  self.bwd_bytes, self.duration,
            self.iat, self.rtt]
    
    def print_flow (self):
        print("flow [{}:{} -> {}:{}] stats => ({}, {}, {}, {}, {})".format(self.nw_src, self.tp_src, self.nw_dst, self.tp_dst, self.fwd_packets, self.fwd_bytes, self.bwd_packets, self.bwd_bytes, self.duration))


## RESPONSE HANDLER
# handler to update flow statistics received in given file 
def _handle_flowstats_received (event):
    stats = flow_stats_to_list(event.stats)
    # log.debug("flow stats received from %s: %s", dpid_to_str(event.connection.dpid), stats)
    for f in stats:
        # flow essential attributes
        match = f['match']
        proto = match['nw_proto']
        nw_src = match['nw_src'][:-3]
        nw_dst = match['nw_dst'][:-3]
        # filter arp msgs
        if proto == 1 or proto == 2:
        # if 'tp_src' not in match.keys():        # happens for ARP msg, need special care
            # log.debug("[ skipping arp msg ]")
            continue
        tp_src = match['tp_src']
        tp_dst = match['tp_dst']
        dpid = event.connection.dpid
        dl_type = match['dl_type']
        packet_count = f['packet_count']
        byte_count = f['byte_count']
        duration = f['duration_sec'] + f['duration_nsec']*1e-9

        # key to find in hash table
        fwd_key = hash(''.join([nw_src, nw_dst, str(tp_src), str(tp_dst), str(dpid)]))
        bwd_key = hash(''.join([nw_dst, nw_src, str(tp_dst), str(tp_src), str(dpid)]))

        # if the fwd flow is present
        if fwd_key in flows.keys():
            # log.debug("Updating forward flow")
            #history[fwd_key] = copy.deepcopy(flows[fwd_key])
            flows[fwd_key].update_forward(packet_count, byte_count, duration)
        # if the bwd flow is also present
        if bwd_key in flows.keys():
            # log.debug("Updating backward flow")
            #history[bwd_key] = copy.deepcopy(flows[bwd_key])
            flows[bwd_key].update_reverse(packet_count, byte_count, duration)
        
        # else create flow entry for both direction flows
        else:
            flows[fwd_key] = Flow(nw_src, nw_dst, tp_src, tp_dst, dpid, proto, dl_type, packet_count, byte_count)
            history[fwd_key] = Flow(nw_src, nw_dst, tp_src, tp_dst, dpid, proto, dl_type , 0, 0)        # zero count history
            
            flows[bwd_key] = Flow(nw_dst, nw_src, tp_dst, tp_src, dpid, proto, dl_type, packet_count, byte_count)
            history[bwd_key] = Flow(nw_src, nw_dst, tp_src, tp_dst, dpid, proto, dl_type, 0, 0)         # zero count history 
   # for key in flows.keys():
   #     flows[key].update_rtt_iat(key)



    

# handler to display port statistics received in JSON format
def _handle_portstats_received (event):
    stats = flow_stats_to_list(event.stats)
    # log.debug("PortStatsReceived from %s: %s", dpid_to_str(event.connection.dpid), stats)



def launch (filename, HOST= None, PORT = None, classifier= None):
    from pox.lib.recoco import Timer

    # attach listeners
    core.openflow.addListenerByName("FlowStatsReceived", _handle_flowstats_received)
    # core.openflow.addListenerByName("PortStatsReceived", _handle_portstats_received)

    # prepare the csv file from given path
    path = "./"+filename
    file = open(path, 'w+')
    writer = csv.writer(file)
    writer.writerow(header)

    # load classifier
    loaded_model = None
    if classifier is not None:
        classifier_path = "/model/" + classifier + ".pth"
        loaded_model = pickle.load(open(classifier_path, 'wb'))

    # data sending over network to data plane/intelligence
    sock = None
    if not (HOST is None or PORT is None):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((str(HOST), int(PORT)))
            log.debug("successfully connected to server")
        except:
            log.debug("failure in socket")

    # timer to execute stats request periodically
    Timer(T, _timer_func, args= [writer, sock, loaded_model], recurring=True)
