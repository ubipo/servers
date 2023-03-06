from dataclasses import field, dataclass
from pathlib import PosixPath
from typing import Any
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
    networks: dict[str, dict[str, Any]] = field(default_factory=dict)
    port_pairs: list[tuple[int, int]] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)
    user: str = "root"
    ulimits: dict[str, Any] = field(default_factory=dict)
    env_files: list[str] = field(default_factory=list)
    secrets: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    stop_grace_period: str = "1m"
    sysctls: dict[str, str] = field(default_factory=dict)
    healthcheck: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, volume_base_dir: PosixPath):
        volume_strings = [
            volume_to_str(volume, volume_base_dir) for volume in self.volumes
        ]
        return {
            "container_name": self.name,
            "image": self.image,
            "volumes": volume_strings,
            "networks": self.networks,
            "ports": [f"{host}:{cont}" for host, cont in self.port_pairs],
            "restart": "unless-stopped",
            "user": "root",
            "environment": self.environment,
            "ulimits": self.ulimits,
            "env_file": [str(path) for path in self.env_files],
            "secrets": self.secrets,
            "depends_on": self.depends_on,
            "stop_grace_period": self.stop_grace_period,
        }


@dataclass(frozen=True)
class ComposeNetwork:
    name: str
    driver: str = "bridge"
    driver_opts: dict[str, Any] = field(default_factory=dict)
    ipam: dict[str, Any] = field(default_factory=dict)
    internal: bool = False

    def to_dict(self):
        return {
            "driver": self.driver,
            "driver_opts": self.driver_opts,
            "ipam": self.ipam,
            "internal": self.internal,
        }


def create_compose_file(
    services: list[ComposeService],
    networks: list[ComposeNetwork],
    volume_base_dir: PosixPath,
):
    compose = {
        "version": "3",
        "services": {
            service.name: service.to_dict(volume_base_dir) for service in services
        },
        "networks": {network.name: network.to_dict() for network in networks},
    }
    file_content = yaml.safe_dump(compose)
    return file_content
