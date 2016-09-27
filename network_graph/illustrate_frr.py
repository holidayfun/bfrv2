from graph_tool.all import Graph, graph_draw, fruchterman_reingold_layout
import json

network = json.load(open('../FRRNetwork.json', 'r'))

g = Graph(directed=False)

vprop_text = g.new_vertex_property("string")
vprop_color = g.new_vertex_property("int")
vprop_size = g.new_vertex_property("int")
vprop_shape = g.new_vertex_property("string")
name_to_vertex = {}

for switch in network['switches']:
    v_switch = g.add_vertex()
    name_to_vertex[switch['name']] = v_switch
    vprop_text[v_switch] = switch['name']
    vprop_color[v_switch] = 1
    vprop_size[v_switch] = 50
    vprop_shape[v_switch] = "hexagon"
    for host in switch['hosts']:
        v_host = g.add_vertex()
        e_link = g.add_edge(v_switch, v_host)
        vprop_text[v_host] = host['name']
        vprop_color[v_host] = 100
        vprop_size[v_host] = 40
        vprop_shape[v_host] = "circle"
        name_to_vertex[host['name']] = v_host
for link in network['switch_links']:
    v_node1 = name_to_vertex[link['node1']['name']]
    v_node2 = name_to_vertex[link['node2']['name']]

    g.add_edge(v_node1, v_node2)

pos = fruchterman_reingold_layout(g, n_iter=1000)

#manually assign positions
pos[name_to_vertex['s1']] = [2, 0]
pos[name_to_vertex['s2']] = [3, 0.5]
pos[name_to_vertex['s3']] = [2, 1]
pos[name_to_vertex['s4']] = [1, 1.5]
pos[name_to_vertex['s5']] = [3, 1.5]
pos[name_to_vertex['s6']] = [2, 2]
pos[name_to_vertex['s7']] = [1, 2.5]
pos[name_to_vertex['s8']] = [3, 2.5]

pos[name_to_vertex['h1']] = [2, -0.7]
pos[name_to_vertex['h2']] = [3.5, 0]
pos[name_to_vertex['h3']] = [1.5, 0.5]
pos[name_to_vertex['h4']] = [0.5, 1]
pos[name_to_vertex['h5']] = [3.7, 1.5]
pos[name_to_vertex['h6']] = [2, 2.7]
pos[name_to_vertex['h7']] = [0.5, 2.9]
pos[name_to_vertex['h8']] = [3.5, 2.9]



graph_draw( g,
            pos,
            vertex_size=vprop_size,
            vertex_shape=vprop_shape,
            vertex_color="black",
            vertex_text=vprop_text,
            vertex_fill_color=vprop_color,
            output_size=(400,400),
            vertex_font_size=15,
            output="frr_network.png")
