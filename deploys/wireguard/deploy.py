from datetime import timedelta
from ipaddress import IPv6Address, IPv6Network

from pyinfra import host, inventory
from pyinfra.api import DeployError
from pyinfra.operations import python

import libdeploys.wireguard.operations as wireguard
import libdeploys.wireguard.facts as wireguard_facts
from util.ini import IniConfig, Section

WG_CONFIG_NUMBER = 0
LISTEN_PORT = 51820
ULA_PREFIX = 64
PERSISTENT_KEEPALIVE = timedelta(minutes=1)


def single_host_net(ipv6_address: IPv6Address):
    return IPv6Network(f"{ipv6_address}/128")


wireguard_hosts = inventory.get_group("wireguard_hosts")

if host not in wireguard_hosts:
    raise DeployError("Host must be in the wireguard_hosts group")

wireguard.install()


def initial_config():
    config: IniConfig = host.get_fact(wireguard_facts.Config, WG_CONFIG_NUMBER)

    if config is None:
        private_key = host.get_fact(wireguard_facts.NewPrivateKey)
        config = IniConfig.from_section_directives(
            (
                "Interface",
                [("PrivateKey", private_key)],
            )
        )
        wireguard.put_config(config, WG_CONFIG_NUMBER)


def after_initial_config():
    config: IniConfig = host.get_fact(wireguard_facts.Config, WG_CONFIG_NUMBER)
    my_ipv6_address: IPv6Address = host.data.get("wg_ipv6_address")
    if my_ipv6_address is None:
        raise DeployError(f"No wg_ipv6_address found for {host.name}")

    interface_section = config.single_section_by_title("Interface")
    interface_section.add_if_not_present(
        ("Address", f"{my_ipv6_address.compressed}/{ULA_PREFIX}")
    )

    my_endpoint_host = host.data.get("wg_endpoint_host")

    if my_endpoint_host is not None:
        # I have an endpoint, so I need to reachable => set port
        interface_section.add_or_replace(("ListenPort", LISTEN_PORT))

    peer_hosts = list(wireguard_hosts)
    peer_hosts.remove(host)

    for peer_host in peer_hosts:
        public_key = peer_host.get_fact(wireguard_facts.PublicKey, WG_CONFIG_NUMBER)
        peer_endpoint_host = peer_host.data.get("wg_endpoint_host")

        peer_ipv6_address = peer_host.data.get("wg_ipv6_address")
        if peer_ipv6_address is None:
            raise DeployError(f"No wg_ipv6_address found for {peer_host.name}")
        allowed_net = single_host_net(peer_ipv6_address)

        section = config.single_section_by_directive("Peer", ("PublicKey", public_key))
        if section is None:
            section = Section.from_directives("Peer", [("PublicKey", public_key)])
            config.add_section(section)

        section.add_if_not_present(("AllowedIPs", allowed_net))

        if peer_endpoint_host is not None:
            endpoint = f"{peer_endpoint_host}:{LISTEN_PORT}"
            section.add_if_not_present(("Endpoint", endpoint))
            interface_section.add_if_not_present(
                (
                    "PreUp",
                    f"until nc -uvzw 2 {peer_endpoint_host} {LISTEN_PORT}; do sleep 2; done",
                )
            )

        if my_endpoint_host is None:
            # I don't have an endpoint, so I'm not always reachable => use
            # keepalive to keep connection open
            section.add_if_not_present(
                ("PersistentKeepalive", int(PERSISTENT_KEEPALIVE.total_seconds()))
            )

    new_config_result = wireguard.put_config(config, WG_CONFIG_NUMBER)
    start_service_result = wireguard.service(
        WG_CONFIG_NUMBER, running=True, enabled=True
    )

    if new_config_result.changed and not start_service_result.changed:
        wireguard.service(WG_CONFIG_NUMBER, reloaded=True)


python.call(initial_config)
python.call(after_initial_config)
