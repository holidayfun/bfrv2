import sys
import os
import json

p4_name = 'bfr'
thrift_client_module = "p4_pd_rpc.bfr"
file_templ = 'table_entries/entries_{0}.bash'

def main():
    network = json.load(open('RingNetwork.json', 'r'))
    #remove old files
    for switch in network['switches']:
        silent_rm(file_templ.format(switch['name']))
    switches = {}

    for switch in network['switches']:
        switches[switch['name']] = switch
        thrift_server = switch['control_network_ip']
        #Einträge für Hosts, die am switch hängen
        action_port = 1 #port nummerierung wi folgt: h1 -> 1, h2 -> 2,...
        for host in switch['hosts']:
            ip_entry = {'ip': host['ip'], 'prefix_len': 32, 'next_hop': host['ip'], 'action_port': action_port}
            forward_entry = {'ip': host['ip'], 'dmac': host['mac']}
            send_frame_entry = {'port': action_port, 'rewrite_mac': host['switch_mac']}
            append_entry_file('echo "Entries for {0}"\n'.format(host['name']), switch['name'])
            add_all_entries(ip_entry, forward_entry, send_frame_entry, switch['name'], thrift_server)
            action_port += 1
    #adding entries for other subnets
    for switch in network['switches']:
        action_port = len(switch['hosts']) + 1
        thrift_server = switch['control_network_ip']
        append_entry_file('echo "Entries for switch interconnects"\n', switch['name'])

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
    except FileNotFoundError:
        pass

def append_entry_file(line, switch_name):
    with open(file_templ.format(switch_name), 'a') as fh:
        fh.write(line)

def handle_cmd(cmd, switch_name, thrift_server, thrift_port=22222):
    append_entry_file('python ../../../cli/pd_cli.py -p {0} -i {1} -s $PWD/../tests/pd_thrift:$PWD/../../../testutils -m "{2}" -c {3}:{4}\n'
                        .format(p4_name, thrift_client_module, cmd, thrift_server, thrift_port), switch_name)

def add_all_entries(ip_entry, forward_entry, send_frame_entry, switch_name, thrift_server, thrift_port=22222):
    add_ip_entry(ip_entry, switch_name, thrift_server, thrift_port)
    add_forward_entry(forward_entry, switch_name, thrift_server, thrift_port)
    add_send_frame_entry(send_frame_entry, switch_name, thrift_server, thrift_port)

def add_ip_entry(entry, switch_name, thrift_server, thrift_port=22222):
    handle_cmd("add_entry ipv4_lpm {entry[ip]} {entry[prefix_len]} set_nhop {entry[next_hop]} {entry[action_port]}".format(entry=entry), switch_name, thrift_server, thrift_port)
def add_forward_entry(entry, switch_name, thrift_server, thrift_port=22222):
    handle_cmd("add_entry forward {entry[ip]} set_dmac {entry[dmac]}".format(entry=entry), switch_name, thrift_server, thrift_port)
def add_send_frame_entry(entry, switch_name, thrift_server, thrift_port=22222):
    handle_cmd("add_entry send_frame {entry[port]} rewrite_mac {entry[rewrite_mac]}".format(entry=entry), switch_name, thrift_server, thrift_port)

def jprint(data):
    print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))


if __name__ == "__main__":
    main()




#adding entries to other swiches in subnet



#jprint(switches)






# #adding IP lpm rules
# if create_entry_file:
#     entry_file.write('echo "IPv4 lpm rules"\n')
#
# entries = [ {'ip': '10.0.3.1', 'prefix_len': 32, 'next_hop': '10.0.3.1', 'action_port': 1},
#             {'ip': '10.0.0.0', 'prefix_len': 16, 'next_hop': '10.0.3.1', 'action_port': 1}]
# for entry in entries:
#     handle_cmd("add_entry ipv4_lpm {entry[ip]} {entry[prefix_len]} set_nhop {entry[next_hop]} {entry[action_port]}".format(entry=entry))
#
# #adding Send Frame rules
# if create_entry_file:
#     entry_file.write('echo "Send Frame rules"\n')
#
# entries = [ {'port': 1, 'rewrite_mac': '00:00:00:00:05:01'}]
# for entry in entries:
#     handle_cmd("add_entry send_frame {entry[port]} rewrite_mac {entry[rewrite_mac]}".format(entry=entry))
#
# #adding Forward rules
# if create_entry_file:
#     entry_file.write('echo "Forward rules"\n')
#
# entries = [ {'ip': '10.0.3.1', 'dmac': '00:00:00:00:02:02'}]
# for entry in entries:
#     handle_cmd("add_entry forward {entry[ip]} set_dmac {entry[dmac]}".format(entry=entry))
#




# s1
# entries = [ {'ip': '10.0.4.0', 'prefix_len': 24, 'next_hop': '10.0.4.2', 'action_port': 1}]
# entries = [ {'port': 1, 'rewrite_mac': '00:00:00:00:01:01'}]
# entries = [ {'ip': '10.0.4.2', 'dmac': '00:00:00:00:02:01'}]
