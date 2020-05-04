total_racks = 13
nodes_per_rack = 10

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
            addr["ip"] = "10.121." + str(84 + (rack_number - 1)+ interface_id*16) + "." + str(2 + node_number + (0 if rack_number == 1 else -1)) + "/28"
            addr["mac"] = "08:00:27:"+"{:02x}".format(rack_number) +":"+"{:02x}".format(node_number) + ":" + "{:02x}".format(interface_id)
            addr["neighbor"]["ip"] = "10.121." + str(84 + (rack_number-1) + interface_id*16) + ".1"
            addr["neighbor"]["asn"] = str(4200858700 + (rack_number -1)* 2 + interface_id + 1)
            addr["neighbor"]["name"] = "management" + str(interface_id*16 + rack_number)
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
    ret += ident + "servie:\n"
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

output = "nodes:\n"
output += generate_node(1, 0, "bootstrap", bgp_asn)

for rack_num in range(1, total_racks+1):
    group = "worknodes"
    for node_num in range(1, nodes_per_rack + 1):
        group = "worknode"
        if rack_num <= 3 and node_num == 1:
            group = "headnode"
        output += generate_node(rack_num, node_num, group, bgp_asn) + "\n"
 
print(output)
