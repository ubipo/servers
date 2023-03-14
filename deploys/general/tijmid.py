# ID server

import inspect
from pyinfra.operations import files, server, systemd
from pyinfra import host, inventory
from deploys.data.tijmid import *
from util.ini import IniConfig


def run():
    server.user(TIJMID_USERNAME, system=True)
    server.shell(f"usermod -aG {TIJMID_USERNAME} nginx")
    unit_file = IniConfig.from_section_directives(
        ("Unit", [("Description", "ID server")]),
        (
            "Service",
            [
                ("Type", "simple"),
                ("User", TIJMID_USERNAME),
                ("Group", TIJMID_USERNAME),
                ("WorkingDirectory", TIJMID_INSTALL_DIR),
                ("StateDirectory", TIJMID_DIR_RELATIVE),
                ("RuntimeDirectory", TIJMID_DIR_RELATIVE),
                ("CacheDirectory", TIJMID_DIR_RELATIVE),
                (
                    "ExecStart",
                    inspect.cleandoc(
                        f"""node {TIJMID_INSTALL_DIR}/main.js \\
                            --listen-socket {TIJMID_RUN_DIR}/sock \\
                            --trust-proxy true \\
                            --base-url https://id.pfiers.net
                        """
                    ),
                ),
                ("Restart", "on-failure"),
            ],
        ),
        ("Install", [("WantedBy", "multi-user.target")]),
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
