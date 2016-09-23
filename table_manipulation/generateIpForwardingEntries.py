import os
import json

p4_name = 'bfr'
thrift_client_module = "p4_pd_rpc.bfr"
file_templ = 'ip_forwarding/entries_{0}'

def main():
    network = json.load(open('../in_use_network.json', 'r'))
    #remove old files
    for switch in network['switches']:
        silent_rm(file_templ.format(switch['name']))
    switches = {}

    for switch in network['switches']:
        switches[switch['name']] = switch
        thrift_server = switch['control_network_ip']
        #Defaults

        append_entry_file("table_set_default ipv4_lpm _drop", switch['name'])
        append_entry_file("table_set_default forward _drop", switch['name'])
        append_entry_file("table_set_default send_frame _drop", switch['name'])
        #Eintraege fuer Hosts, die am switch haengen
        action_port = 1 #port nummerierung wie folgt: h1 -> 1, h2 -> 2,...
        for host in switch['hosts']:
            ip_entry = {'ip': host['ip'], 'prefix_len': 32, 'next_hop': host['ip'], 'action_port': action_port}
            forward_entry = {'ip': host['ip'], 'dmac': host['mac']}
            send_frame_entry = {'port': action_port, 'rewrite_mac': host['switch_mac']}
            add_all_entries(ip_entry, forward_entry, send_frame_entry, switch['name'], thrift_server)
            action_port += 1
    #adding entries for other subnets
    for switch in network['switches']:
        action_port = len(switch['hosts']) + 1
        thrift_server = switch['control_network_ip']

        for link in network['switch_links']:
            if switch['name'] in [link['node1']['name'], link['node2']['name']]:
                if link['node1']['name'] == switch['name']:
                    other_switch = switches[link['node2']['name']]
                    ld_switch = link['node1']
                    ld_other_switch = link['node2']
                else:
                    other_switch = switches[link['node1']['name']]
                    ld_switch = link['node2']
                    ld_other_switch = link['node1']

                ip_entry = {'ip': other_switch['subnet_ip'], 'prefix_len': other_switch['prefix_len'], 'next_hop': ld_other_switch['ip'], 'action_port': action_port}
                forward_entry = {'ip': ld_other_switch['ip'], 'dmac': ld_other_switch['mac']}
                send_frame_entry = {'port': action_port, 'rewrite_mac': ld_switch['mac']}
                add_all_entries(ip_entry, forward_entry, send_frame_entry, switch['name'], thrift_server)

                action_port += 1


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

def add_all_entries(ip_entry, forward_entry, send_frame_entry, switch_name, thrift_server, thrift_port=22222):
    add_ip_entry(ip_entry, switch_name, thrift_server, thrift_port)
    add_forward_entry(forward_entry, switch_name, thrift_server, thrift_port)
    add_send_frame_entry(send_frame_entry, switch_name, thrift_server, thrift_port)

def add_ip_entry(entry, switch_name, thrift_server, thrift_port=22222):
    handle_cmd("table_add ipv4_lpm set_nhop {entry[ip]}/{entry[prefix_len]} => {entry[next_hop]} {entry[action_port]:04d}".format(entry=entry), switch_name, thrift_server, thrift_port)
def add_forward_entry(entry, switch_name, thrift_server, thrift_port=22222):
    handle_cmd("table_add forward set_dmac {entry[ip]} => {entry[dmac]}".format(entry=entry), switch_name, thrift_server, thrift_port)
def add_send_frame_entry(entry, switch_name, thrift_server, thrift_port=22222):
    handle_cmd("table_add send_frame rewrite_mac {entry[port]} => {entry[rewrite_mac]}".format(entry=entry), switch_name, thrift_server, thrift_port)

def jprint(data):
    print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))


if __name__ == "__main__":
    main()
