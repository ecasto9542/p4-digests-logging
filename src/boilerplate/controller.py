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

# Global variables
digest_message_num_bytes = 8


class SimpleSwitchAPI(runtime_CLI.RuntimeAPI):
    @staticmethod
    def get_thrift_services():
        return [("simple_switch", SimpleSwitch.Client)]

    def __init__(self, pre_type, standard_client, mc_client, sswitch_client):
        runtime_CLI.RuntimeAPI.__init__(self, pre_type,
                                        standard_client, mc_client)
        self.sswitch_client = sswitch_client

def on_digest_recv(msg):
    #unpacking digest header, "num" is the number of messages in the digest
    _, _, ctx_id, list_id, buffer_id, num = struct.unpack("<iQiiQi", msg[:32])

    ### Insert the receiving logic below ###
    #trimming off the digest header
    msg = msg[32:]

    offset = digest_message_num_bytes

    # loop through the messages in the digest
    for msg in range(num):
        msg_copy = msg[0:]
        #### unpack the message


        msg = msg[offset:]

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
