from dataclasses import field, dataclass
from pathlib import PosixPath
import yaml


def make_absolute(base: PosixPath, path: PosixPath | str):
    if isinstance(path, str):
        return path

    if path.is_absolute():
        return path

    return base / path


def volume_to_str(volume: tuple[PosixPath | str, str], volume_base_dir: PosixPath):
    host, cont = volume
    return f"{make_absolute(volume_base_dir, host)}:{cont}"


@dataclass(frozen=True)
class ComposeService:
    name: str
    image: str
    volumes: list[tuple[PosixPath | str, str]] = field(default_factory=list)
    port_pairs: list[tuple[int, int]] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)
    user: str = "root"

    def to_dict(self, volume_base_dir: PosixPath):
        volume_strings = [
            volume_to_str(volume, volume_base_dir) for volume in self.volumes
        ]
        return {
            "container_name": self.name,
            "image": self.image,
            "volumes": volume_strings,
            "ports": [f"{host}:{cont}" for host, cont in self.port_pairs],
            "restart": "unless-stopped",
            "user": "root",
            "environment": self.environment,
        }


def create_compose_file(services: list[ComposeService], volume_base_dir: PosixPath):
    compose = {
        "version": "3",
        "services": {
            service.name: service.to_dict(volume_base_dir) for service in services
        },
    }
    file_content = yaml.safe_dump(compose)
    return file_content
