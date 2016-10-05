import os
import json
import math
from graph_tool.all import Graph

p4_name = 'bfr'
thrift_client_module = "p4_pd_rpc.bfr"
file_templ = 'bier_te/bift_entries_{0}'


def main():
    network = json.load(open('../in_use_network.json', 'r'))
    num_switches = len(network['switches'])
    max_port_num = 4
    #we need num_switches + num_switches * max_port_num bits
    bitsring_len = int(math.pow(2, math.ceil(math.log(num_switches * (max_port_num + 1), 2))))

    #Generate graph representation of network
    g = Graph(directed=False)
    name_to_vertex = {}
    vprop_name = g.new_vertex_property("string")
    vprop_dev = g.new_vertex_property("int")
    vprop_bp = g.new_vertex_property("int")
    bp = 1
    for switch in network['switches']:
        v_switch = g.add_vertex()
        name_to_vertex[switch['name']] = v_switch
        vprop_name[v_switch] = switch['name']
        vprop_dev[v_switch] = 1
        vprop_bp[v_switch] = bp
        bp += 1
        for host in switch['hosts']:
            v_host = g.add_vertex()
            g.add_edge(v_switch, v_host)
            name_to_vertex[host['name']] = v_host
            vprop_name[v_host] = host['name']
            vprop_dev[v_host] = 2

    for link in network['switch_links']:
        v_node1 = name_to_vertex[link['node1']['name']]
        v_node2 = name_to_vertex[link['node2']['name']]
        g.add_edge(v_node1, v_node2)

    #remove old files
    for switch in network['switches']:
        silent_rm(file_templ.format(switch['name']))
    switches_dict = {}
    switches_list = []
    for switch in network['switches']:
        switches_dict[switch['name']] = switch
        switches_list.append(switch)
        #thrift_server = switch['control_network_ip']
        #Default drop packet
        #append_entry_file("table_set_default bift _drop", switch['name'])

    for i in range(0, num_switches):
        bits_of_interest = ['0'] * bitsring_len
        bits_of_interest[bitsring_len - i - 1] = '1'

        append_entry_file("table_add bift local_decap {0} =>".format(i + 1), switches_list[i]['name'])
        #Erste X ports sind hosts
        port_offset = len(switch['hosts']) + 1
        for j in range(0, max_port_num):
            bit_pos = (i * max_port_num) + j + num_switches
            bits_of_interest[bitsring_len - bit_pos - 1] = '1'

            append_entry_file("table_add bift forward_connected {0} => {1}".format(bit_pos + 1, port_offset + j), switches_list[i]['name'])

        append_entry_file("table_add get_bits_of_interest save_bits_of_interest 0/0 => 0b" + "".join(bits_of_interest), switches_list[i]['name'])

        #NNHs
        v_switch = name_to_vertex[switches_list[i]['name']]
        print("NNHs of {0}".format(switches_list[i]['name']))
        nnhs = ['0'] * bitsring_len

        for nh in v_switch.out_neighbours():
            for nnh in nh.out_neighbours():
                if nnh != v_switch and vprop_dev[nnh] == 1:
                    nnhs[bitsring_len - vprop_bp[nnh]] = '1'

        print("".join(nnhs))

        #append_entry_file("table_add bits_of_interest save_bits_of_interest 1/1 => " + "".join(bits_of_interest), switches_list[i]['name'])


def silent_rm(path):
    try:
        os.remove(path)
    except:
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
