from getpass import getpass
from ipaddress import IPv6Network
from pathlib import Path
import sys


# Necessary to make imports from deploy scripts work
sys.path.append(Path(__file__).parent)

passwords = {}


def password_for(host: str):
    if host not in passwords:
        passwords[host] = getpass(f"Password for {host}: ")
    return passwords[host]


hosts = [
    (
        "cannelloni",
        {
            "fqdn": "cannelloni.pfiers.net",
            "ssh_hostname": "10.0.0.20",
            "ssh_user": "root",
            "ssh_password": password_for("cannelloni"),
            "ssh_allow_agent": False,
        },
    ),
    # (
    #     "cannelloni",
    #     {
    #         "ssh_hostname": "localhost",
    #         "ssh_port": 2222,
    #         "ssh_user": "root",
    #         "ssh_password": password_for("cannelloni"),
    #         "ssh_allow_agent": False,
    #     },
    # ),
    (
        "linguine",
        {
            "fqdn": "linguine.pfiers.net",
            "ssh_hostname": "167.235.58.79",
            "ssh_user": "root",
            "ssh_password": password_for("linguine"),
            "ssh_allow_agent": False,
        },
    ),
]

tls_pfiers_wildcard_leader_hosts = ["linguine"]  # Creates the cert
tls_pfiers_wildcard_follower_hosts = ["cannelloni"]  # Syncs cert from leader

nginx_http_upstream_hosts = ["cannelloni"]
nginx_http_proxy_hosts = ["linguine"]

app_hosts = ["cannelloni"]

zabbix_agent_hosts = ["cannelloni", "linguine"]

# Generated from cannelloni enp2s0 with https://cd34.com/rfc4193/
ULA_NET = IPv6Network("fd61:1b78:37c8::/48")
ULA_PREFIX = 64
ULA_NETS = ULA_NET.subnets(new_prefix=ULA_PREFIX)
WG_NET = next(ULA_NETS)

wireguard_hosts = [
    (
        "linguine",
        {
            "wg_ipv6_address": WG_NET[1],
            "wg_endpoint_host": "linguine.pfiers.net",
        },
    ),
    ("cannelloni", {"wg_ipv6_address": WG_NET[2]}),
]
