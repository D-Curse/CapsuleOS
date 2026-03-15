import os
import random

BRIDGE_NAME = "capsule0"
BRIDGE_IP = "10.10.0.1"
SUBNET = "10.10.0"

def setup_bridge():
    if os.path.exists(f"/sys/class/net/{BRIDGE_NAME}"):
        return
    
    os.system(f"ip link add {BRIDGE_NAME} type bridge")
    os.system(f"ip addr add {BRIDGE_IP}/24 dev {BRIDGE_NAME}")
    os.system(f"ip link set {BRIDGE_NAME} up")
    
    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
    os.system(f"iptables -t nat -A POSTROUTING -s {SUBNET}.0/24 ! -o {BRIDGE_NAME} -j MASQUERADE")
    
def allocate_ip():
    return f"{SUBNET}.{random.randint(2, 254)}"

def setup_container_network(cid, pid, container_ip):
    veth_host = f"veth_{cid[:8]}"
    veth_cont = f"veth0"
    
    os.system(f"ip link add {veth_host} type veth peer name {veth_cont}")
    
    os.system(f"ip link set {veth_host} master {BRIDGE_NAME}")
    os.system(f"ip link set {veth_host} up")
    
    os.system(f"ip link set {veth_cont} netns {pid}")
    
    os.system(f"nsenter --net=/proc/{pid}/ns/net -- ip addr add {container_ip}/24 dev {veth_cont}")
    os.system(f"nsenter --net=/proc/{pid}/ns/net -- ip link set {veth_cont} up")
    os.system(f"nsenter --net=/proc/{pid}/ns/net -- ip link set lo up")
    os.system(f"nsenter --net=/proc/{pid}/ns/net -- ip route add default via {BRIDGE_IP}")
    
def teardown_container_network(cid):
    veth_host = f"veth_{cid[:8]}"
    os.system(f"ip link del {veth_host} 2>/dev/null")