#!/usr/bin/env python2

import sys
sys.path.append("/home/hartmann/behavioral-model/tools")
import nnpy
import struct
import re
import json
import argparse
import bmpy_utils as utils
from subprocess import Popen, PIPE
parser = argparse.ArgumentParser(description='BM nanomsg event logger client')
parser.add_argument('--socket', help='IPC socket to which to subscribe',
                    action="store", required=False)
parser.add_argument('--json', help='JSON description of P4 program [deprecated]',
                    action="store", required=False)
parser.add_argument('--thrift-port', help='Thrift server port for table updates',
                    type=int, action="store", default=9090)
parser.add_argument('--thrift-ip', help='Thrift IP address for table updates',
                    type=str, action="store", default='localhost')

args = parser.parse_args()

class NameMap:
    def __init__(self):
        self.names = {}

    def load_names(self, json_cfg):
        self.names = {}
        json_ = json.loads(json_cfg)

        for type_ in {"header_type", "header", "parser",
                      "deparser", "action", "pipeline", "checksum"}:
            json_list = json_[type_ + "s"]
            for obj in json_list:
                self.names[(type_, obj["id"])] = obj["name"]

        for pipeline in json_["pipelines"]:
            tables = pipeline["tables"]
            for obj in tables:
                self.names[("table", obj["id"])] = obj["name"]

            conds = pipeline["conditionals"]
            for obj in conds:
                self.names[("condition", obj["id"])] = obj["name"]

    def get_name(self, type_, id_):
        return self.names.get( (type_, id_), None )

name_map = NameMap()

def name_lookup(type_, id_):
    return name_map.get_name(type_, id_)

def json_init(client):
    json_cfg = utils.get_json_config(standard_client=client)
    name_map.load_names(json_cfg)

def recv_msgs(socket_addr, client):
    def get_msg_type(msg):
        type_ = str(msg[:4])
        return type_

    json_init(client)

    sub = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
    sub.connect(socket_addr)
    sub.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, '')

    #ID of the last inserted handle
    last_handle = -1

    while True:
        msg = sub.recv()
        msg_type = get_msg_type(msg)
        msg = msg[4:]
        if msg_type[:3] != "PRT":
            print("Unsupported message type: " + msg_type)
            continue
        #extract header and data part
        hdr = msg[:8]
        data = msg[28:]
        #extract information from the header
        switch_id, num_statuses = struct.unpack('iI', hdr)

        #unpack status information
        for i in range(0, num_statuses):
            tup = struct.unpack('ii', data[(0+i*8):(8+i*8)])
            port = tup[0]
            status = tup[1]
            print("{0} Status s{1}: Port {2} is {3}".format(msg_type, switch_id+1, port, "UP" if status else "DOWN"))

        if num_statuses > 1:
            print("more than one status change, no p4 action is taken")
            continue

        thrift_port = 10000
        thrift_ip = "100.0.0.{0}".format(102+ 2*switch_id)

        num_switches = 8
        num_ports = 4
        bit_pos = num_switches + num_ports * switch_id + port - 1
        if status == 1:
            command = "table_delete frr_indication {0}".format(last_handle)
            last_handle = -1
        else:
            command = "table_add frr_indication save_bp 0/0 => {0}".format(bit_pos)
        print(command)
        ps_echo = Popen(['echo', command], stdout=PIPE)
        ps_cli = Popen(['/home/hartmann/behavioral-model/targets/bfrv2/cli/sswitch_CLI.py',
                        '--thrift-port', str(thrift_port),
                        '--thrift-ip', thrift_ip], stdin=ps_echo.stdout, stdout=PIPE)

        ps_echo.stdout.close()
        output = ps_cli.communicate()[0]
        match = re.search("handle (\d+)", output)
        if match:
            inserted_handle = match.group(1)
            print("Entry handle: " + str(inserted_handle))
            last_handle = inserted_handle

def main():
    deprecated_args = ["json"]
    for a in deprecated_args:
        if getattr(args, a) is not None:
            print "Command line option '--{}' is deprecated".format(a),
            print "and will be ignored"

    client = utils.thrift_connect_standard(args.thrift_ip, args.thrift_port)
    info = client.bm_mgmt_get_info()
    socket_addr = info.elogger_socket
    if socket_addr is None:
        print "The event logger is not enabled on the switch,",
        print "run with '--nanolog <ip addr>'"
        sys.exit(1)
    if args.socket is not None:
        socket_addr = args.socket
    else:
        print "'--socket' not provided, using", socket_addr,
        print "(obtained from switch)"

    recv_msgs(socket_addr, client)

if __name__ == "__main__":
    main()
