#!/usr/bin/python3
from netmiko import ConnectHandler
from jinja2 import Template
from getpass import getpass
import requests
import os

def get_ix(ix_options):
    ix_ids = {
        'AMSIX': 26,
        'DECIX': 31,
        'LINX': 18,
        'GLOBALIX': 1088,
        'LSIX': 1308
    }
    while True:
        ix_choice=input(f"Select the IX [{ ','.join(ix_options) }]:")
        if ix_choice in ix_options:
            return ix_choice,ix_ids[ix_choice]
        else:
            print("Error! Invalid IX Name")
            
def get_peer_asn():            
    while True:
        peer_asn = input("Enter Peer ASN: ")
        try:
          peer_asn = int(peer_asn)
          return peer_asn
        except ValueError:
          print("Invalid input. Please enter a valid integer.")

def get_peer_details(peer_asn,ix_id,api_token):
    headers = {"Authorization": "Api-Key " + f"{api_token}"}
    net_data_url = f"https://www.peeringdb.com/api/net?asn={peer_asn}"
    net_response = requests.get(net_data_url, headers=headers)

    if net_response.status_code != 200:
        raise Exception(f"Failed to retrieve net data: { net_response.status_code }")
    
    net_data = net_response.json()
    net_id = net_data['data'][0]['id']
    net_name = net_data['data'][0]['name']
    

    netixlan_data_url = f"https://www.peeringdb.com/api/netixlan?net_id={net_id}"
    netixlan_response = requests.get(netixlan_data_url, headers=headers)

    if netixlan_response.status_code != 200:
        raise Exception(f"Failed to retrieve netixlan data: { netixlan_response.status_code }")
    
    netixlan_data = netixlan_response.json()['data']

    ix_peer_ipv4 = []
    ix_peer_ipv6 = []
    for dictionary in netixlan_data:
        if dictionary['ix_id'] == ix_id:
            ix_peer_ipv4.append(dictionary['ipaddr4'])
            ix_peer_ipv6.append(dictionary['ipaddr6'])

    return net_name,ix_peer_ipv4,ix_peer_ipv6
    
def main():
    api_token = os.getenv("PEERINGDB_API_TOKEN")

    if os.getenv("RADIUS_PASSWORD"):
        password = os.getenv("RADIUS_PASSWORD")
    else:
        password = getpass("Enter your password:")

    er1_ams1_ip = os.getenv("ER1_AMS1")
    er1_ams2_ip = os.getenv("ER1_AMS2")

    ix_options = ['AMSIX','DECIX','LINX','GLOBALIX','LSIX']

    device = {
    "device_type": "juniper_junos",
    "host": "",               #will set er1.ams1 or er1.ams2 ip according to ix choice from the user
    "username": "nradil",
    "password": password,
    "port": "22",
    "ssh_config_file": "./ssh_config",
    }

    #Collect ix name from user as input and also return ix id based on ix name
    ix,ix_id = get_ix(ix_options)

    #collect peer asn from user only strict integer
    peer_asn = get_peer_asn()

    #collect peer network name,peer ip addresses at the given ix point using peeringdb api
    net_name,ix_peer_ipv4,ix_peer_ipv6 = get_peer_details(peer_asn,ix_id,api_token)
    
    #setting device ip according to ix choice
    if ix in ['AMSIX','DECIX','GLOBALIX']:
        device['host'] = f'{er1_ams2_ip}'
    elif ix in ['LINX','LSIX']:
        device['host'] = f'{er1_ams1_ip}'

    #setting bgp groups
    if ix == "LINX":
        ipv4_bgp_group = f"{ix}-INET4"
        ipv6_bgp_group = f"{ix}-INET6-NEW"
    else:
        ipv4_bgp_group = ix
        ipv6_bgp_group = f"{ix}-INET6"
    
    #Setting template configuration file and setup our configuration
    peering_template_file = "peering_template.j2"
    with open(peering_template_file) as f:
       peering_template = Template(f.read(), keep_trailing_newline=True)
    
    ipv4_peering_configs = ""
    for ip_addr in ix_peer_ipv4:
       ipv4_peering_config = peering_template.render(
            BGP_GROUP = ipv4_bgp_group,              
            PEER_IP = ip_addr,
            PEER_NAME = net_name,
            PEER_ASN = peer_asn
        )
       ipv4_peering_configs+=ipv4_peering_config + "\n"

    ipv6_peering_configs = ""
    for ip_addr in ix_peer_ipv6:
       ipv6_peering_config = peering_template.render(
            BGP_GROUP = ipv6_bgp_group,              
            PEER_IP = ip_addr,
            PEER_NAME = net_name,
            PEER_ASN = peer_asn
        )
       ipv6_peering_configs+=ipv6_peering_config + "\n"   

    ipv4_config_set =  "\n".join(ipv4_peering_configs.splitlines())
    ipv6_config_set = "\n".join(ipv6_peering_configs.splitlines())
    config_set = ipv4_config_set + "\n" + ipv6_config_set 


    #Establish session with router and send configuration
    with ConnectHandler(**device) as ch:
          ch.config_mode()
          output = ch.send_config_set(config_set)
          compare = ch.send_command('show | compare')
          print(output + "\n" + compare)
          confirm = input("\nDo you want to commit these changes? (yes/no): ").strip().lower()
          if confirm == 'yes':
              commit_output = ch.commit()  # Commit the changes and exit configuration mode
              print(commit_output)              
          else:
             # Commit configuration changes            
             print("Changes not confirmed. Exiting without committing.")


if __name__ == "__main__":
    main()



