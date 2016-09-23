import json
num_switches = 8
hosts_per_switch = 1

network = { 'name': 'FRRNetwork',
            'switches': []}

#generate Switches with a number of hosts connected to them
for i in range(1,num_switches + 1):
    s = {   'name'  : 's{0}'.format(i),
            'number': i,
            'ip': '10.0.{0}.1'.format(i),
            'mac' : 'aa:00:00:00:{0:02d}:1'.format(i),
            'control_network_ip' : '100.0.0.%s' % (100 + 2 * i),
            'subnet_ip' : '10.0.{0}.0'.format(i),
            'prefix_len' : 24,
            'hosts' : []
            }

    for j in range(1, num_switches * hosts_per_switch + 1, num_switches):
        host_num = j + i - 1
        print(host_num)
        h = {   'name':'h{0}'.format(host_num),
                'number': j,
                'ip': '10.0.{0}.{1}'.format(i, host_num + 1),
                'mac' : 'aa:00:00:00:{0:02d}:{1:02d}'.format(i, host_num + 1),
                'switch_addr': '10.0.{0}.{1}'.format(i, 100 + host_num + 1),
                'switch_mac' : 'aa:aa:00:00:{0:02d}:{1:02d}'.format(i, host_num + 1)
                }
        s['hosts'].append(h)

    network['switches'].append(s)

switch_links = []
#generate inter-switch links
custom_links = [['s1', 's2'], ['s1', 's3'], ['s2', 's5'],['s3', 's4'],
                ['s3', 's5'],['s3', 's6'],['s4', 's7'],['s5', 's8'],['s6', 's7'],['s6', 's8']]
for i in range(0, len(custom_links)):
    link = custom_links[i]

    switch_links.append({ 'node1': {'name' : link[0],
                                    'ip' : '20.0.0.{0}'.format(2 * i + 1),
                                    'mac' : 'aa:dd:00:00:00:{0:02d}'.format(2 * i + 1)},
                          'node2': {'name' : link[1],
                                     'ip' : '20.0.0.{0}'.format(2 * i + 2),
                                     'mac' : 'aa:dd:00:00:00:{0:02d}'.format(2 * i + 2)}})

#print(switch_links)

def get_switch_by_name(name):
    for switch in network['switches']:
        if switch['name'] == name:
            return switch
    return None
network['switch_links'] = switch_links
#print(json.dumps(switch_links, sort_keys=True, indent=4, separators=(',', ': ')))
#print(json.dumps(inter_switch_links, sort_keys=True, indent=4, separators=(',', ': ')))
#print(json.dumps(s, sort_keys=True, indent=4, separators=(',', ': ')))
#print(links)

with open('{0}.json'.format(network['name']), 'w') as network_file:
    json.dump(network, network_file, sort_keys=True, indent=4, separators=(',', ': '))
