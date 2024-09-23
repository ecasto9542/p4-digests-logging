#!/usr/bin/env python3

import socket
import datetime
import math
import struct
import pandas as pd
import sys
import time
import argparse
import json
import csv
sys.path.append('../')
from utilities.pmu_csv_parser import parse_csv_data
from datetime import datetime

index = 0
csv_sent_time_data = [["index", "sent_at"]]
def generate_packet(time, voltages, angles, settings={"pmu_measurement_bytes": 8, "destination_ip": "192.168.0.100", "destination_port": 4712}):
    # Define the PMU packet as a byte string
    datetime_str = str(time)[:26]
    global index
    try:
        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

    # 2 byte

    sync = b'\xAA\x01'
    #sync = index.to_bytes(2, 'big')


    # 2 byte, 44 for 32 bit values of PMU, 40 for 16 bit values of PMU
    # 36 - 8 + 8 * number of PMUs || 36 - 8 + 4 * number PMUs
    frame_size = b'\x00\x24'

    # 2 byte, 12 for this
    id_code = b'\x00\x0C'

    # 4 byte
    soc = int(dt.strftime("%s")).to_bytes(4, 'big')
    #print(dt.strftime("%s"))
    # 4 byte
    frac_sec = dt.microsecond.to_bytes(4, 'big')
    # 2 byte (no errors)
    stat = b'\x00\x00'

    # 4 or 8 byte x number of phasors (see doc, 8 is for float)
    voltage_bytes0 = struct.pack('>f', voltages[0])
    angle_bytes0 = struct.pack('>f', math.radians(angles[0]))

    voltage_bytes1 = struct.pack('>f', voltages[1])
    angle_bytes1 = struct.pack('>f', math.radians(angles[1]))

    voltage_bytes2 = struct.pack('>f', voltages[2])
    angle_bytes2 = struct.pack('>f', math.radians(angles[2]))

    # 24 bytes total, first 8 bytes for first phasor, next 8 bytes for next phasor, and so on
    phasors = voltage_bytes0 + angle_bytes0 + voltage_bytes1 + angle_bytes1 + voltage_bytes2 + angle_bytes2


    # 2 byte, assumed 60
    freq = b'\x09\xC4'

    # 2 byte
    dfreq = b'\x00\x00'

    # 4 byte
    analog = b'\x00\x00\x00\x00'

    # 2 byte
    digital = b'\x00\x00'

    # 2 byte
    chk = b'\x00\x00'

    pmu_packet = sync + frame_size + id_code + soc + frac_sec + \
        stat + phasors + freq + dfreq + analog + digital + chk

    # Set the destination IP address and port number
    destination_ip = settings["destination_ip"]
    destination_port = 4712

    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #write to csv file the index and the time
    csv_sent_time_data.append([index, datetime.now()])

    # Send the PMU packet to the destination IP address and port number
    udp_socket.sendto(pmu_packet, (destination_ip, destination_port))

    # Close the UDP socket
    udp_socket.close()


def parse_console_args(parser):
    parser.add_argument('filename')
    parser.add_argument('--ip', default="10.0.2.2")
    parser.add_argument('--port', default=4712)
    parser.add_argument('--num_packets', default=100)
    parser.add_argument('--drop_indexes', default='./missing-data.json')

    return parser.parse_args()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
                        prog='pmu-packet-sender',
                        description='Sends pmu packets',
                        epilog='Text at the bottom of help')

    args = parse_console_args(parser)

    drop_indexes_file = open(args.drop_indexes)

    drop_indexes = json.load(drop_indexes_file)

    pmu_csv_data = parse_csv_data(
        args.filename,
        "TimeTag",
        ["Magnitude01", "Magnitude02", "Magnitude03"],
        ["Angle01", "Angle02", "Angle03"]
    )

    num_to_send = len(pmu_csv_data["times"])
    if int(args.num_packets) > 0:
        num_to_send = int(args.num_packets)

    for i in range(num_to_send):
        if i == 0:
            print("Start transmission at: " + str(datetime.now()))
        #sending to loopback as opposed to switch
        settings_obj = {"destination_ip": "127.0.0.1" if i in drop_indexes else  args.ip, "destination_port": int(args.port)}
        time.sleep(0.017)
        generate_packet(pmu_csv_data["times"][i], [pmu_csv_data["magnitudes"][0][i], pmu_csv_data["magnitudes"][1][i], pmu_csv_data["magnitudes"][2][i]], [pmu_csv_data["phase_angles"][0][i], pmu_csv_data["phase_angles"][1][i], pmu_csv_data["phase_angles"][2][i]], settings_obj)

    # generate_packets()
