from pyinfra.api import operation
from pyinfra.api.exceptions import DeployError
from pyinfra import host
from pyinfra.facts.deb import DebPackages
from pyinfra.facts.pacman import PacmanPackages
from pyinfra.operations import apt, pacman, files, systemd

from util.ini import IniConfig


@operation
def install():
    """Installs wireguard"""

    if host.get_fact(DebPackages):
        yield from apt.packages(
            packages=["wireguard"],
            update=True,
        )
    elif host.get_fact(PacmanPackages):
        yield from pacman.packages(["wireguard-tools"], update=True)
    else:
        raise DeployError(
            f"Neither apt nor pacman were found. Cannot install wireguard."
        )


@operation
def service(
    config_number: int, running=True, restarted=False, enabled=None, reloaded=False
):
    """Manages the wg-quick service with the given config number"""

    yield from systemd.service(
        f"wg-quick@wg{config_number}",
        running=running,
        restarted=restarted,
        enabled=enabled,
        reloaded=reloaded,
    )


@operation
def syncconf(config_number: int):
    """Sync the config with the given number to the running interface"""

    yield f"wg syncconf wg{config_number} /etc/wireguard/wg{config_number}.conf"


@operation
def put_config(config: IniConfig, config_number: int):
    """Uploads the given config to /etc/wgX.conf for the given config_number X"""

    yield from files.put(
        config.to_string_io(), f"/etc/wireguard/wg{config_number}.conf"
    )


@operation
def generate_private_key():
    """Generates the private key"""

    yield "wg genkey > tee /etc/wireguard/private.key"
    yield "chmod 600 /etc/wireguard/private.key"
