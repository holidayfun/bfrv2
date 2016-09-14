#!/usr/bin/python


from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.node import Node, RemoteController, Switch
from p4_mininet import P4Switch, P4Host
import argparse
#from time import sleep
import json


network = json.load(open('RingNetwork.json', 'r'))


def main(args):
    sw_path = args.behavioral_exe
    thrift_port = args.thrift_port
    thrift_port = 10000
    json_path = args.json
    pcap_dump = args.pcap_dump
    topo = NetworkTopo(sw_path, json_path, thrift_port, pcap_dump)


    net = OwnMininet(topo = topo, host= P4Host,
                        switch=P4Router, controller=None)
    #adding host routes to controller to be able to connect to redis DB
    net_switches =[net.get(switch['name'])
                                for switch in network['switches']]
    c0 = net.addController('c0', controller=InbandController)
    net.configureControlNetwork()
    for s in net_switches:
        s.setHostRoute('192.168.122.42', s.connectionsTo(c0)[0][0])

    net.start()

    for switch in network['switches']:
        net_switch = net.get(switch['name'])
        for host in switch['hosts']:
            net_host = net.get(host['name'])
            net_host.setARP(host['switch_addr'], host['switch_mac'])
            net_host.setDefaultRoute("dev eth0 via %s" % host['switch_addr'])

            link_to_switch = net_host.connectionsTo(net_switch)[0]
            net_switch.setMAC(host['switch_mac'], intf=link_to_switch[1])
            net_switch.setIP(host['switch_addr'], intf=link_to_switch[1])
    #Add IPs and macs for inter-switch links
    for link in network['switch_links']:
        ld_sw1 = link['node1']
        ld_sw2 = link['node2']

        net_sw1 = net.get(ld_sw1['name'])
        net_sw2 = net.get(ld_sw2['name'])

        net_link = net_sw1.connectionsTo(net_sw2)[0]

        net_sw1.setIP(ld_sw1['ip'], intf=net_link[0])
        net_sw1.setMAC(ld_sw1['mac'], intf=net_link[0])

        net_sw2.setIP(ld_sw2['ip'], intf=net_link[1])
        net_sw2.setMAC(ld_sw2['mac'], intf=net_link[1])

    #remove entries from routing tables
    for net_switch in net_switches:
        net_switch.cmd("ip route del 10.0.0.0/8")
        net_switch.cmd("ip route del 10.0.0.0/8")
        net_switch.cmd("ip route del 20.0.0.0/8")
        net_switch.cmd("ip route del 20.0.0.0/8")
    #remove entries from routing tables
    for switch in network['switches']:
	for host in switch['hosts']:
	    net_host = net.get(host['name'])
	    net_host.cmd("ip route del 10.0.0.0/8")
    CLI(net)
    net.stop()

class InbandController(RemoteController):
    def checkListening(self):
	"Overridden to do nothing."
	return

class NetworkTopo(Topo):
    """generate the network topology"""
    def __init__(self, sw_path, json_path, thrift_port, pcap_dump, **opts):
        Topo.__init__(self, **opts)

        for switch in network['switches']:
	    print("switch {0} with thrift_port {1}".format(switch['name'], thrift_port))
            s = self.addSwitch(switch['name'],
				sw_path=sw_path,
				json_path=json_path,
				thrift_port=thrift_port,
				pcap_dump=pcap_dump,
				inNamespace = True)
            for host in switch['hosts']:
                h = self.addHost(host['name'], ip=host['ip'], mac=host['mac'])
                self.addLink(s, h)


        for link in network['switch_links']:
            self.addLink(link['node1']['name'], link['node2']['name'])

class OwnMininet(Mininet):
    def configureControlNetwork(self):
	info("configuring control network.")
	n = 0
	for controller in self.controllers:
	    for switch in self.switches:
	            sw_to_ctrl = self.addLink(switch,controller)
		    controller.setIP( '100.0.0.%s' % (100 + 2 * n + 1), intf=sw_to_ctrl.intf2)
		    switch.setIP(     '100.0.0.%s' % (100 + 2 * n + 2), intf=sw_to_ctrl.intf1)

		    controller.setMAC('00:00:00:0c:00:%02d' % (n + 1), intf=sw_to_ctrl.intf2)
		    switch.setMAC('00:00:00:0c:%02d:01' % (n + 1), intf=sw_to_ctrl.intf1)
        	    controller.setHostRoute('100.0.0.%s' % (100 + 2 * n + 2), sw_to_ctrl.intf2)
	            n += 1

class P4Router(P4Switch):
    """P4 virtual Router"""
    listenerPort = 11111
    dpidLen = 16
    #we pretend to not be a switch, so mininet assumes we are a host
    def defaultIntf(self):
        return Node.defaultIntf(self)

    def __init__( self, name, sw_path="dc_full", json_path=None,
			thrift_port=None,
			pcap_dump=True,
			verbose=True,
			device_id=None,
			enable_debugger=True,
			**kwargs ):
        #P4Switch.__init__(self, name, sw_path, json_path, thrift_port,
	#			pcap_dump, verbose, device_id,
	#			enable_debugger, **kwargs)
        Switch.__init__(self, name, **kwargs)

        assert(sw_path)
        assert(json_path)
        self.sw_path = sw_path
        self.json_path = json_path
        self.verbose = verbose
        self.logfile = '/tmp/p4s.%s.log' % self.name
        self.thrift_port = thrift_port
        self.pcap_dump = pcap_dump
        self.enable_debugger = enable_debugger
        self.nanomsg = "ipc:///bm-%d-log.ipc" % self.device_id
        if device_id is not None:
            self.device_id = device_id
            P4Switch.device_id = max(P4Switch.device_id, device_id)
        else:
            self.device_id = P4Switch.device_id
            P4Switch.device_id += 1

    def start( self, controllers ):
        "Start up a new P4 Router"
        args = [self.sw_path]
        #args.extend( ['--name', self.name] )
        #args.extend( ['--dpid', self.dpid] )
        for port, intf in self.intfs.items():
            if not intf.IP():
                args.extend( ['-i', str(port) + "@" + intf.name] )
        #args.extend(['--pd-server', '40.0.0.{0}:{1}'.format(100 + 2 * int(self.dpid), self.thrift_port)] )
        #args.extend( ['--p4nsdb', '192.168.122.42:6379'] )

        if self.pcap_dump:
            args.append( '--pcap')
	if self.thrift_port:
	    args.extend(['--thrift-port', str(self.thrift_port)])
	if self.nanomsg:
            print(self.nanomsg)
	    args.extend(['--nanolog', self.nanomsg])
	args.extend(['--device-id', str(self.device_id)])
	P4Switch.device_id += 1
	args.append(self.json_path)
	if self.enable_debugger:
	    args.append('--debugger')

        #logging
        args.extend(['--log-file', self.logfile])
        args.append('--log-flush')

        print(' '.join(args) + '  2>&1 </dev/null &')
        self.cmd(' '.join(args) + '  2>&1 </dev/null &' , verbose=True)
    def stop(self):
        self.cmd('kill %' + self.sw_path)
        self.cmd('wait')
        self.deleteIntfs()
if __name__ == "__main__":
    setLogLevel('debug')
    parser = argparse.ArgumentParser(description='Mininet demo')
    parser.add_argument('--behavioral-exe', help='Path to behavioral executable', type=str, action="store", required=True)
    parser.add_argument('--thrift-port', help='Thrift server port for table updates', type=int, action="store", default=22222)
    parser.add_argument('--json', help='Path to JSON config file', type=str, action="store",required=True)
    parser.add_argument('--pcap-dump', help='Dump packets on interfaces to pcap files', type=str,action="store", required=False, default=False)
    args = parser.parse_args()

    main(args)
