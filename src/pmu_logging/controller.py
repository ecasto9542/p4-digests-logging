#!/usr/bin/env python3
import runtime_CLI
from sswitch_runtime import SimpleSwitch
from sswitch_runtime.ttypes import *
import struct
import nnpy
import socket
import math
from threading import Thread
from queue import Queue
import time
import datetime
import csv
import ipaddress

# Global variables
digest_message_num_bytes = 40
delayed_packet_count = 0
counter = 0
class SimpleSwitchAPI(runtime_CLI.RuntimeAPI):
    @staticmethod
    def get_thrift_services():
        return [("simple_switch", SimpleSwitch.Client)]

    def __init__(self, pre_type, standard_client, mc_client, sswitch_client):
        runtime_CLI.RuntimeAPI.__init__(self, pre_type,
                                        standard_client, mc_client)
        self.sswitch_client = sswitch_client

def parse_phasors(phasor_data, settings={"num_phasors": 1, "pmu_measurement_bytes": 8}):
    phasor = {
        "magnitude": struct.unpack('>f', phasor_data[0:4])[0],
        "angle": math.degrees(struct.unpack('>f', phasor_data[4:])[0]),
    }
    return [phasor]

def on_digest_recv(msg):
    print('received a message')
    global delayed_packet_count
    #unpacking digest header, "num" is the number of messages in the digest
    _, _, ctx_id, list_id, buffer_id, num = struct.unpack("<iQiiQi", msg[:32])

    ### Insert the receiving logic below ###
    #trimming off the digest header
    msg = msg[32:]

    offset = digest_message_num_bytes

    

    # loop through the messages in the digest
    for m in range(num):
        print('got something')
        #TODO: log a delayed packet to a database here after extracting out the necessary info
        delayed_packet_count=delayed_packet_count+1
        #### unpack the message
        msg_copy = msg[0:]
        
        digest_packet = {
        "soc0": msg[0:4],
        "fracsec0": msg[4:8],
        "phasors0": msg[8:16],
        "curr_soc": msg[16:20],
        "curr_fracsec": msg[20:24],
        "src_ip": msg[24:28],
        "dest_ip": msg[28:32]
        }

        soc0= int.from_bytes(msg_copy[0:4],byteorder="big")
        fracsec0= int.from_bytes(msg_copy[4:8],byteorder="big")
        temp = int.from_bytes(msg_copy[8:12], byteorder='big')

        phasors0= parse_phasors(msg_copy[8:16])
        curr_soc= int.from_bytes(msg_copy[16:20],byteorder="big")
        curr_fracsec= int.from_bytes(msg_copy[20:24],byteorder="big")
        src_ip = ipaddress.ip_address(msg_copy[24:28])
        dest_ip = ipaddress.ip_address(msg_copy[28:32])

        print("NUM DELAYED TOTAL: " + str(delayed_packet_count))

        datetime_obj = datetime.datetime.fromtimestamp(curr_soc + (curr_fracsec / 1000000))
        print("Datetime:", datetime_obj)
        print("Phasors: ", phasors0)
        print("Source ip:", src_ip)
        print("Dest ip:", dest_ip)
        with open('log.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                writer.writerow(["Datetime", "Phasor 1", "Source IP", "Destination IP"])
            writer.writerow([datetime_obj, phasors0, src_ip, dest_ip])
        msg = msg[offset:]
        
        #return digest_packet

def setup():
    args = runtime_CLI.get_parser().parse_args()

    args.pre = runtime_CLI.PreType.SimplePreLAG

    services = runtime_CLI.RuntimeAPI.get_thrift_services(args.pre)
    services.extend(SimpleSwitchAPI.get_thrift_services())

    standard_client, mc_client, sswitch_client = runtime_CLI.thrift_connect(
        args.thrift_ip, args.thrift_port, services
    )

    runtime_CLI.load_json_config(standard_client, args.json)
    runtime_api = SimpleSwitchAPI(
        args.pre, standard_client, mc_client, sswitch_client)

    sub = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
    socket = runtime_api.client.bm_mgmt_get_info().notifications_socket

    print("socket is : " + str(socket))
    sub.connect(socket)
    sub.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, '')

    return runtime_api, sub

def listen_for_new_digests(q):
    global counter
    while counter < 10:
        counter += 1
        event_data = q.get()
        on_digest_recv(event_data)
        q.task_done()

def queue_digests(digest_queue, sub):
    message = sub.recv()
    digest_queue.put(message)

if __name__ == "__main__":
    runtime_api, sub = setup()

    digest_message_queue = Queue()

    # Create the thread to listen for digest messages
    digest_message_thread = Thread(target=queue_digests, args=(digest_message_queue, sub))
    digest_message_thread.daemon = True
    digest_message_thread.start()

    listen_for_new_digests(digest_message_queue)
