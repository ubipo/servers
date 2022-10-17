from pathlib import PosixPath
from pyinfra import inventory, host
from util.app_ports import AppPorts
from compose_apps.create_app import create_app
from util.compose import ComposeService


def run():
    create_app(
        "baserow",
        [
            ComposeService(
                name="baserow",
                image="baserow/baserow:1.12",
                volumes=[
                    (PosixPath("data"), "/baserow/data"),
                ],
                port_pairs=[(AppPorts.baserow.value, 80)],
                environment={"BASEROW_PUBLIC_URL": "http://baserow.pfiers.net"},
            )
        ],
    )


app_hosts = inventory.get_group("app_hosts")
if host not in app_hosts:
    print(f"Skipping baserow deploy on {host.name} because it is not an app host")
else:
    run()
