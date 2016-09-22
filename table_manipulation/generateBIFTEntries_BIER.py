import sys
import os
import json

p4_name = 'bfr'
thrift_client_module = "p4_pd_rpc.bfr"
file_templ = 'bier/bift_entries_{0}'
bitsring_len = 16

def main():
    network = json.load(open('RingNetwork.json', 'r'))
    num_switches = len(network['switches'])
    #remove old files
    for switch in network['switches']:
        silent_rm(file_templ.format(switch['name']))
    switches_dict = {}
    switches_list = []
    for switch in network['switches']:
        switches_dict[switch['name']] = switch
        switches_list.append(switch)
        thrift_server = switch['control_network_ip']
        #Default drop packet
        append_entry_file("table_set_default bift _drop", switch['name'])

    for i in range(0, num_switches):
        next_bitstring = ['0'] * bitsring_len
        prev_bitstring = ['0'] * bitsring_len
        #here in RingNetwork:
        #the next num_switches/2 bfrs are reached through neigbour switch+1
        #the previous num_switches/2 bfrs are reached through neigbour switch-1
        next_nbr = switches_list[(i + 1) % num_switches]
        prev_nbr = switches_list[(i - 1) % num_switches]
        for j in range(0, int(num_switches/2)):
            next_bitstring[-switches_list[(i + 1 + j) % num_switches]['number']] = '1'
        #no switch should be in prev and next, so a little special case is needed
        for j in range(0, int(num_switches/2) - ((num_switches + 1) % 2)):
            prev_bitstring[-switches_list[(i - 1 - j) % num_switches]['number']] = '1'
        #here the next switch is always on port 4
        #and the prev switch is always on port 3
        next_port = 4
        prev_port = 3

        for j in range(0, int(num_switches/2)):
            bfr_id = switches_list[(i + 1 + j) % num_switches]['number']
            next_entry = {"bfr_id" : bfr_id, "nbr_port" : next_port, 'bitstring' : "".join(next_bitstring)}
            add_bift_entry(next_entry, switches_list[i]['name'], thrift_server)
        for j in range(0, int(num_switches/2) - ((num_switches + 1) % 2)):
            bfr_id = switches_list[(i - 1 - j) % num_switches]['number']
            prev_entry = {"bfr_id" : bfr_id,"nbr_port" : prev_port, 'bitstring' : "".join(prev_bitstring)}
            add_bift_entry(prev_entry, switches_list[i]['name'], thrift_server)

def silent_rm(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
def append_entry_file(line, switch_name):
    with open(file_templ.format(switch_name), 'a') as fh:
        fh.write(line + "\n")
def handle_cmd(cmd, switch_name, thrift_server, thrift_port=22222):
    append_entry_file('{0}'.format(cmd), switch_name)
def add_all_entries(bift_entry, switch_name, thrift_server, thrift_port=22222):
    add_bift_entry(bift_entry, switch_name, thrift_server, thrift_port)
def add_bift_entry(entry, switch_name, thrift_server, thrift_port=22222):
    handle_cmd("table_add bift bift_action {entry[bfr_id]} => 0b{entry[bitstring]} {entry[nbr_port]}".format(entry=entry), switch_name, thrift_server, thrift_port)

def jprint(data):
    print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))

if __name__ == "__main__":
    main()
