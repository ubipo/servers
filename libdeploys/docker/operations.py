from pathlib import Path
from pyinfra.api import operation, DeployError
from pyinfra.operations import server, apt, pacman, systemd
from pyinfra import host
from pyinfra.facts import server as server_facts
from colorama import init as colorama_init
from colorama import Fore, Style
import sys


@operation
def install():
    dist = host.get_fact(server_facts.LinuxDistribution)
    dist_id = dist["release_meta"]["ID"]

    if dist_id == "debian":
        docker_deps = ["ca-certificates", "curl", "gnupg", "lsb-release"]
        # https://github.com/docker/for-linux/issues/1199#issuecomment-1431571192
        docker_deps.append("apparmor")
        yield from apt.packages(
            packages=docker_deps,
            update=True,
        )

        yield from server.script(
            str(Path(__file__).parent / "files/install_docker_keys.sh")
        )

        yield from apt.packages(
            packages=[
                "docker-ce",
                "docker-ce-cli",
                "containerd.io",
                "docker-compose-plugin",
            ],
            update=True,
        )

        colorama_init()
        print(
            f"{Fore.YELLOW}A reboot might be necessary for apparmor (and by extension docker) to work.{Style.RESET_ALL}",
            file=sys.stderr,
        )
    elif dist_id == "arch":
        yield from pacman.packages(["docker", "docker-compose"], update=True)
    else:
        raise DeployError(
            f"Unsupported distribution for automated docker install: {dist_id=}"
        )

    yield from systemd.service("docker", running=True, enabled=True)
