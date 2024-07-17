#!/usr/bin/python3
from netmiko import ConnectHandler
from jinja2 import Template
import csv
import os
from getpass import getpass

source_file = "switch_ports.csv"
int_template_file = "interface_temp.j2"

with open(int_template_file) as f:
   int_template = Template(f.read(), keep_trailing_newline=True)

interface_configs = ""

with open(source_file) as f:
   reader = csv.DictReader(f)
   for row in reader:
        interface_config = int_template.render(
            Interface = row["Interface"],
            Description = row["Company"],
            Vlan = row["Vlan"]
        )
        interface_configs+=interface_config
        
username = os.getenv("RADIUS_USER")
if os.getenv("RADIUS_PASSWORD"):
   password = os.getenv("RADIUS_PASSWORD")
else:
   password = getpass("Enter your password:")

switch_ip = os.getenv("SWITCH_IP")

device = {
    "device_type": "cisco_ios",
    "host": f"{switch_ip}",
    "username": username,
    "password": password,
    "port": "22",
    "ssh_config_file": "./ssh_config",
}


with ConnectHandler(**device) as ch:
   config_set = interface_configs.split("\n")
   output = ch.send_config_set(config_set)
   print(output)

