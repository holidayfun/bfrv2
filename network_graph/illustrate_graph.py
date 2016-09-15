from graph_tool.all import *
import json

network = json.load(open('../RingNetwork.json', 'r'))

g = Graph(directed=False)

vprop_text = g.new_vertex_property("string")
vprop_color = g.new_vertex_property("int")

name_to_vertex = {}


for switch in network['switches']:
    v_switch = g.add_vertex()
    name_to_vertex[switch['name']] = v_switch
    vprop_text[v_switch] = switch['name']
    vprop_color[v_switch] = 1
    for host in switch['hosts']:
        v_host = g.add_vertex()
        e_link = g.add_edge(v_switch, v_host)
        vprop_text[v_host] = host['name']
        vprop_color[v_host] = 100
for link in network['switch_links']:
    v_node1 = name_to_vertex[link['node1']['name']]
    v_node2 = name_to_vertex[link['node2']['name']]

    g.add_edge(v_node1, v_node2)

print(name_to_vertex)

pos = fruchterman_reingold_layout(g, n_iter=1000)
graph_draw( g,
            pos,
            vertex_text=vprop_text,
            vertex_fill_color=vprop_color,
            vertex_font_size=18,
            output_size=(400,400),
            output="two-nodes.png")
