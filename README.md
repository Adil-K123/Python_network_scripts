# Python_network_scripts

There is two scripts in this repository which automates some repeative tasks in network

Scripts Overview
1. member_port_config.py
This script fetches data from a CSV file and configures switch ports accordingly. It leverages Jinja2 templates to generate the configuration commands.

Features:

Reads data from a specified CSV file.
Uses Jinja2 templates to create configuration commands.
Automates the process of configuring switch ports.
Uses netmiko for ssh session with router

2. ix_peer_config.py
This script collects Peer ASN and IX location , fetches peer details from PeeringDB using the PeeringDB API, and then generate and complete router configuration for peering with the specified peers.

Features:

Collects Peer ASN and IX location details from the user.
Fetches peer details from PeeringDB using the PeeringDB API.
Uses Jinja2 templates to generate peering configuration commands for routers.
Uses netmiko for ssh session with router