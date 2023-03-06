from typing import Optional
from pyinfra.api import operation, DeployError
from pyinfra.facts import server as server_facts
from pyinfra.operations import apt, pacman, files, server, systemd
from pyinfra import host

from libdeploys.zabbix.common import create_api_call_command, ApiCredentials
from libdeploys.zabbix.facts import User


AGENTD_CONFIG_PATH = "/etc/zabbix/zabbix_agentd.conf"
AGENTD_SERVICE = "zabbix-agent"


@operation
def install_agent():
    dist = host.get_fact(server_facts.LinuxDistribution)
    dist_id = dist["release_meta"]["ID"]
    if dist_id == "debian":
        version = dist["release_meta"]["VERSION_ID"]
        assert version == "11", f"Unsupported debian version: {version}"
        deb = "zabbix-release_6.2-4%2Bdebian11_all.deb"
        yield from files.download(
            f"https://repo.zabbix.com/zabbix/6.2/debian/pool/main/z/zabbix-release/{deb}",
            f"/tmp/{deb}",
        )
        yield from server.shell(f"dpkg -i /tmp/{deb}")
        yield from apt.packages(["zabbix-agent"], update=True)
    elif dist_id == "arch":
        yield from pacman.packages(["zabbix-agent"], update=True)
    else:
        raise DeployError(
            f"Unsupported distribution for automated zabbix agent install: {dist_id}"
        )

    yield from systemd.service(
        AGENTD_SERVICE,
        running=True,
        enabled=True,
    )


@operation
def configure_agent(
    hostname: str,
    server_address_passive: Optional[str] = None,
    nbro_passive_agents: Optional[int] = 0,
    server_address_active: Optional[str] = None,
):
    yield from files.line(
        path=AGENTD_CONFIG_PATH,
        line=r"^Hostname=.*$",
        replace=f"Hostname={hostname}",
    )
    yield from files.line(
        path=AGENTD_CONFIG_PATH,
        line=r"^Server=.*$",
        replace=f"Server={server_address_passive or ''}",
    )
    yield from files.line(
        path=AGENTD_CONFIG_PATH,
        line=r"^ServerActive=.*$",
        replace=f"ServerActive={server_address_active or ''}",
    )
    yield from files.line(
        path=AGENTD_CONFIG_PATH,
        line=r"^StartAgents=.*$",
        replace=f"StartAgents={nbro_passive_agents}",
    )
    yield from systemd.service(
        AGENTD_SERVICE,
        running=True,
        restarted=True,
        enabled=True,
    )


@operation
def api_call(credentials: ApiCredentials, endpoint: str, parameters: dict):
    yield from create_api_call_command(credentials, endpoint, parameters)


@operation
# User must be in at least one group (otherwise api throws error)
def create_user(
    credentials: ApiCredentials,
    username: str,
    password: str,
    roleid: str,
    usrgrps: list[dict],
):
    user = host.get_fact(User, credentials, username=username)
    if user is None:
        yield from api_call(
            credentials,
            "user.create",
            {
                "username": "provisioning",
                "passwd": password,
                "roleid": roleid,
                "usrgrps": usrgrps,
            },
        )
