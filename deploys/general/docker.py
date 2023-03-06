from libdeploys import docker
from pyinfra import host
from pyinfra.api import DeployError


docker.install()

is_functional = host.get_fact(docker.IsFunctional)
if is_functional:
    print("Docker is functioning properly")
else:
    raise DeployError("Docker is not functioning properly")
