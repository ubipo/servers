from io import StringIO
from pathlib import PosixPath
from pyinfra.operations import files
from deploys import docker_compose
from util.compose import ComposeService, create_compose_file

CONFIG_DIR = PosixPath("/etc/compose-apps")
DATA_DIR = PosixPath("/srv/compose-apps")


def create_app(
    name: str,
    services: list[ComposeService],
):
    config_dir = CONFIG_DIR / name
    data_dir = DATA_DIR / name
    files.directory(config_dir, mode=755, _sudo=True)
    files.directory(data_dir, mode=755, _sudo=True)

    compose_file_content = create_compose_file(services, volume_base_dir=data_dir)
    compose_file_path = config_dir / "docker-compose.yml"
    files.put(
        StringIO(compose_file_content),
        str(compose_file_path),
        _sudo=True,
    )

    docker_compose.up(compose_file_path, _sudo=True)
