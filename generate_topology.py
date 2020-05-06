import jinja2

total_racks = 7 # virtualbox limits number of NICs to 8 
nodes_per_rack = 20

bgp_asn = "4200858801"

def generate_net_address(interface_type, rack_number, node_number):
    n_interface = 1 if interface_type == "service" else 2
    ret = []
    for interface_id in range(0, n_interface):
        addr = {}
        addr["neighbor"] = {}
        if interface_type == "service":
            addr["ip"] = "10.65.0." + str((rack_number-1) * 16 + node_number + (1 if rack_number==1 else -1))
        else:
            addr["ip_noslash"] = "10.121." + str(84 + (rack_number - 1)+ interface_id*16) + "." + str(2 + node_number + (0 if rack_number == 1 else -1))
            addr["ip"] = addr["ip_noslash"] + "/24"
            addr["mac"] = "08:00:27:"+"{:02x}".format(rack_number) +":"+"{:02x}".format(node_number) + ":" + "{:02x}".format(interface_id)
            addr["neighbor"]["ip"] = "10.121." + str(84 + (rack_number-1) + interface_id*16) + ".1"
            addr["neighbor"]["asn"] = str(4200858700 + (rack_number -1)* 2 + interface_id + 1)
            addr["neighbor"]["name"] = "management" + str(interface_id*16 + rack_number)
        addr["rack_num"] = rack_number
        addr["node_num"] = node_number
        ret.append(addr)
    return ret

def generate_node(rack_number, node_number, group, bgp_asn):
    ident = " " * 2
    ret = ident + "- host: r" + str(rack_number) + "n" + str(node_number) + "\n"
    ident = " " * 4
    ret = ret + ident + "group: " + group + "s\n"
    ret = ret + ident + "hardware_profile: " + group + "\n"
    ret = ret + ident + "host_vars:" + "\n"
    ident = " " * 6
    ret = ret + ident + "bgp:" + "\n"
    ident = " " * 8
    ret = ret + ident + "asn: " + bgp_asn + "\n"
    ident = " " * 6
    ret = ret + ident + "interfaces:" + "\n"
    ident = " " * 8
    ret += ident + "service:\n"
    ident = " " * 10
    service_addr = generate_net_address("service", rack_number, node_number)[0]
    ret = ret + ident + "ip: " + service_addr["ip"] + "\n"
    ident = " " * 8
    ret = ret + ident + "transit:" + "\n"
    transit_addr = generate_net_address("transit", rack_number, node_number)
    for i in range(0,2):
        ident = " " * 10
        ret = ret + ident + "- ip: " + transit_addr[i]["ip"] + "\n"
        ret += " " * 12 + "mac: '" + transit_addr[i]["mac"] + "'\n"
        ret += " " * 12 + "neighbor:\n"
        ret += " " * 14 + "ip: " + transit_addr[i]["neighbor"]["ip"] + "\n"
        ret += " " * 14 + "asn: " + transit_addr[i]["neighbor"]["asn"]+"\n"
        ret += " " * 14 + "name: " + transit_addr[i]["neighbor"]["name"] + "\n"

    ret += " " * 6 + "run_list:" + "\n"
    if group == "bootstrap":
        ret += " " * 8 + "- role[bootstrap]\n"
    elif group == "headnode":
        ret += " " * 8 + "- role[" + group + "]\n"
    else:
        ret += " " * 8 + "- role[worknode]\n"
        ret += " " * 8 + "- role[storagenode]\n"
    return ret

def generate_netplan(total_racks):
    ret = ""
    ret += "network:\n"
    ret += " "*2 + "version: 2\n"
    ret += " " * 2 + "ethernets:\n"
    ret += " " * 4 + "eth0:\n"
    ret += " " * 6 + "dhcp4: true\n"
    for i in range(1, total_racks+1):
        ret += " " * 4 + "eth" + str(i) + ":\n"
        ret += " " * 6 + "addresses:\n"
        ret += " " * 8 + "- 10.121." + str(84 + i - 1) + ".1/24"
    return ret

def generate_networkvm_bird_conf(total_racks, nodes_per_rack):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template("bird_network.conf.jinja2")

    net_addrs = []
    for rack_num in range(1, total_racks + 1):
        for node_num in range(0, nodes_per_rack + 1):
            if rack_num != 1 and node_num == 0:
                continue
            net_addr = generate_net_address("transit", rack_num, node_num)
            net_addrs.append(net_addr)
    out = template.render(net_addrs = net_addrs)
    return out

def generate_networkvm_netplan(total_racks):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template("network.yaml.jinja2")
    out = template.render(num_racks = total_racks)
    return out

def generate_topology(total_racks, nodes_per_rack):
    output = "nodes:\n"
    output += generate_node(1, 0, "bootstrap", bgp_asn)
    for rack_num in range(1, total_racks+1):
        group = "worknodes"
        for node_num in range(1, nodes_per_rack + 1):
            group = "worknode"
            if rack_num <= 3 and node_num == 1:
                group = "headnode"
            output += generate_node(rack_num, node_num, group, bgp_asn) + "\n"
    return output

topology = generate_topology(total_racks, nodes_per_rack)
with open("./topology/topology.yml", "w") as fh:
    fh.write(topology)

networkvm_bird_conf = generate_networkvm_bird_conf(total_racks, nodes_per_rack)
with open("./network/bird/network.conf", "w") as fh:
    fh.write(networkvm_bird_conf)

networkvm_netplan = generate_networkvm_netplan(total_racks)
with open("./network/netplan/network.yaml", "w") as fh:
    fh.write(networkvm_netplan)


