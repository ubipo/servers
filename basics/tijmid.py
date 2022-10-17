# ID server

from pyinfra.operations import files, server, systemd
from pyinfra import host, inventory
from basics.tijmid_data import (
    TIJMID_DATA_DIR,
    TIJMID_DB_PATH,
    TIJMID_INSTALL_DIR,
    TIJMID_RUN_DIR,
    TIJMID_USERNAME,
    TIJMID_RUN_DIRE_RELATIVE,
)
from util.ini import IniConfig


def run():
    server.user(TIJMID_USERNAME, system=True)
    server.shell(f"usermod -aG {TIJMID_USERNAME} nginx")
    files.directory(
        TIJMID_DATA_DIR, user=TIJMID_USERNAME, group=TIJMID_USERNAME, mode=770
    )
    unit_file = IniConfig.from_section_directives(
        [
            ("Unit", [("Description", "ID server")]),
            (
                "Service",
                [
                    ("Type", "simple"),
                    ("User", TIJMID_USERNAME),
                    ("Group", TIJMID_USERNAME),
                    ("WorkingDirectory", TIJMID_INSTALL_DIR),
                    ("RuntimeDirectory", TIJMID_RUN_DIRE_RELATIVE),
                    (
                        "ExecStart",
                        f"node {TIJMID_INSTALL_DIR}/dist/main.mjs --listen-socket {TIJMID_RUN_DIR}/sock --db {TIJMID_DB_PATH} --pid-file {TIJMID_RUN_DIR}/pid --trust-proxy true",
                    ),
                    ("Restart", "on-failure"),
                ],
            ),
        ]
    )
    files.put(
        unit_file.to_string_io(),
        str(f"/etc/systemd/system/tijmid.service"),
        mode=644,
    )

    systemd.service("tijmid.service", running=True, enabled=True, daemon_reload=True)


app_hosts = inventory.get_group("app_hosts")
if host not in app_hosts:
    print(f"Skipping tijmid deploy on {host.name} because it is not an app host")
else:
    run()
