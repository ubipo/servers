from io import StringIO
from pathlib import PosixPath

import libdeploys.compose_app as compose_app
from pyinfra import host, inventory
from pyinfra.operations import files, pip, apt, pacman
from pyinfra.facts import server as server_facts
from libdeploys.zabbix.common import ApiCredentials
from deploys.data.app_ports import AppPorts
from util.compose import ComposeNetwork, ComposeService
from util.secrets import get_secrets
from libdeploys import zabbix
from deploys.data.zabbix import *


# Adapted from:
# https://github.com/zabbix/zabbix-docker/blob/6.2/docker-compose_v3_alpine_pgsql_latest.yaml
def run():
    secrets = get_secrets()
    admin_password = secrets[ADMIN_PASSWORD_SECRET_KEY]
    provisioning_password = secrets[PROVISIONING_PASSWORD_SECRET_KEY]
    assert type(admin_password) is str

    config_dir, data_dir = compose_app.create_app_dirs("zabbix")

    db_env_path = config_dir / "db.env"
    files.put(
        StringIO(
            "\n".join(
                [
                    f"DB_SERVER_HOST={DB_SERVICE_NAME}",
                    "POSTGRES_USER=zabbix",
                    "POSTGRES_PASSWORD=zabbix",
                    "POSTGRES_DB=zabbix",
                ]
            )
        ),
        str(db_env_path),
        _sudo=True,
    )

    web_env_path = config_dir / "web.env"
    files.put(
        StringIO(
            "\n".join(
                [
                    f"ZBX_SERVER_HOST={SERVER_SERVICE_NAME}",
                    f"ZBX_SERVER_NAME={SERVER_WEB_NAME}",
                    "ZBX_SERVER_PORT=10051",
                ]
            )
        ),
        str(web_env_path),
        _sudo=True,
    )

    compose_app.create_compose_app(
        "zabbix",
        [
            ComposeService(
                name=SERVER_SERVICE_NAME,
                image="zabbix/zabbix-server-pgsql",
                volumes=[
                    (PosixPath("alertscripts"), "/usr/lib/zabbix/alertscripts:ro"),
                    (
                        PosixPath("externalscripts"),
                        "/usr/lib/zabbix/externalscripts:ro",
                    ),
                    (PosixPath("dbscripts"), "/usr/lib/zabbix/dbscripts:ro"),
                    (PosixPath("export"), "/var/lib/zabbix/export:rw"),
                    (PosixPath("modules"), "/var/lib/zabbix/modules:ro"),
                    (PosixPath("enc"), "/var/lib/zabbix/enc:ro"),
                    (PosixPath("ssh_keys"), "/var/lib/zabbix/ssh_keys:ro"),
                    (PosixPath("mibs"), "/var/lib/zabbix/mibs:ro"),
                    (PosixPath("snmptraps"), "/var/lib/zabbix/snmptraps:ro"),
                ],
                ulimits={
                    "nproc": 65535,
                    "nofile": {"soft": 20000, "hard": 40000},
                },
                env_files=[db_env_path],
                depends_on=["zabbix-postgres"],
                networks={
                    NETWORK_BACKEND: {
                        "aliases": [SERVER_SERVICE_NAME],
                    },
                    NETWORK_FRONTEND: {},
                },
                sysctls={
                    "net.ipv4.ip_local_port_range": "1024 65000",
                    "net.ipv4.conf.all.accept_redirects": "0",
                    "net.ipv4.conf.all.secure_redirects": "0",
                    "net.ipv4.conf.all.send_redirects": "0",
                },
                port_pairs=[(AppPorts.zabbix_server.value, 10051)],
                environment={"BASEROW_PUBLIC_URL": "http://baserow.pfiers.net"},
            ),
            ComposeService(
                name=DB_SERVICE_NAME,
                image="postgres:14-alpine",
                volumes=[
                    (PosixPath("postgresql-data"), "/var/lib/postgresql/data:rw"),
                ],
                env_files=[db_env_path],
                networks={
                    NETWORK_BACKEND: {
                        "aliases": [DB_SERVICE_NAME],
                    },
                },
            ),
            ComposeService(
                name=WEB_SERVICE_NAME,
                image="zabbix/zabbix-web-nginx-pgsql",
                volumes=[
                    (PosixPath("modules"), "/usr/share/zabbix/modules/:ro"),
                ],
                env_files=[db_env_path, web_env_path],
                depends_on=[SERVER_SERVICE_NAME, DB_SERVICE_NAME],
                healthcheck={
                    "test": ["CMD", "curl", "-f", "http://localhost:8080/ping"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 3,
                    "start_period": "30s",
                },
                networks={
                    NETWORK_BACKEND: {
                        "aliases": [WEB_SERVICE_NAME],
                    },
                    NETWORK_FRONTEND: {},
                },
                sysctls={
                    "net.core.somaxconn": 65535,
                },
                port_pairs=[(AppPorts.zabbix_web.value, 8080)],
            ),
        ],
        networks=[
            ComposeNetwork(
                name=NETWORK_BACKEND,
                driver="bridge",
                driver_opts={
                    "com.docker.network.enable_ipv6": "false",
                },
                ipam={
                    "driver": "default",
                    "config": [
                        {"subnet": "172.16.238.0/24"},
                    ],
                },
            ),
            ComposeNetwork(
                name=NETWORK_FRONTEND,
                driver="bridge",
                driver_opts={
                    "com.docker.network.enable_ipv6": "false",
                },
                ipam={
                    "driver": "default",
                    "config": [{"subnet": "172.16.239.0/24"}],
                },
                internal=True,
            ),
        ],
    )

    dist = host.get_fact(server_facts.LinuxDistribution)
    dist_id = dist["release_meta"]["ID"]
    if dist_id == "debian":
        apt.packages(["python3-pip"], update=True)
    elif dist_id == "arch":
        pacman.packages(["python-pip"], update=True)

    pip.packages(packages=["zabbix-api"])
    zabbix.create_user(
        ApiCredentials.DEFAULT(), "provisioning", provisioning_password, "3", ["7"]
    )


app_hosts = inventory.get_group("app_hosts")
if host not in app_hosts:
    print(f"Skipping zabbix deploy on {host.name} because it is not an app host")
else:
    run()
