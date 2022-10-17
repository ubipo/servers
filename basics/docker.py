from pathlib import Path
from pyinfra.operations import server, apt, pacman, systemd
from pyinfra import host
from pyinfra.facts import server as server_facts

dist = host.get_fact(server_facts.LinuxDistribution)
dist_id = dist["release_meta"]["ID"]

if dist_id == "debian":
    apt.packages(
        packages=["ca-certificates", "curl", "gnupg", "lsb-release"],
        update=True,
        _sudo=True,
    )

    server.script(
        str(Path(__file__).parent / "files/install_docker_keys.sh"), _sudo=True
    )

    apt.packages(
        packages=[
            "docker-ce",
            "docker-ce-cli",
            "containerd.io",
            "docker-compose-plugin",
        ],
        update=True,
        _sudo=True,
    )
elif dist_id == "arch":
    pacman.packages(["docker", "docker-compose"], update=True, _sudo=True)
else:
    raise Exception(f"Unsupported Linux distribution ({dist_id=})")

systemd.service("docker", running=True, enabled=True, _sudo=True)
