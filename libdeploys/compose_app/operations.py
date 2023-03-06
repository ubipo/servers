from io import StringIO
from pathlib import PosixPath
from typing import Optional
from pyinfra import inventory, host
from pyinfra.api import operation
from pyinfra.operations import files
from libdeploys import docker_compose
from util.compose import ComposeService, create_compose_file

CONFIG_DIR = PosixPath("/etc/compose-apps")
DATA_DIR = PosixPath("/srv/compose-apps")


@operation
def create_app_dirs(name: str):
    config_dir = CONFIG_DIR / name
    data_dir = DATA_DIR / name
    yield from files.directory(config_dir, mode=755, _sudo=True)
    yield from files.directory(data_dir, mode=755, _sudo=True)
    return config_dir, data_dir


@operation
def create_compose_app(
    name: str,
    services: list[ComposeService],
    networks: Optional[list[str]] = None,
    only_in_group: Optional[str] = None,
):
    if networks is None:
        networks = []

    if only_in_group is not None:
        app_hosts = inventory.get_group(only_in_group)
        if host not in app_hosts:
            print(
                f"Skipping {name} deploy on {host.name} because it is not in group {only_in_group}"
            )
            return

    config_dir, data_dir = yield from create_app_dirs(name)

    compose_file_content = create_compose_file(
        services, networks, volume_base_dir=data_dir
    )
    compose_file_path = config_dir / "docker-compose.yml"
    yield from files.put(
        StringIO(compose_file_content),
        str(compose_file_path),
        _sudo=True,
    )

    yield from docker_compose.up(compose_file_path, _sudo=True)
