import json
from syncthing import Syncthing
from pyinfra.api import operation
from pyinfra.api.exceptions import DeployError
from pyinfra import host
from pyinfra.facts.deb import DebPackages
from pyinfra.facts.pacman import PacmanPackages
from pyinfra.facts.server import Users, User
from pyinfra.operations import apt, server, pacman, systemd
from deploys.syncthing.common import create_request_curl_command, SyncthingConfig
import deploys.syncthing.facts as facts


@operation
def install():
    """Installs syncthing"""

    if host.get_fact(DebPackages):
        yield from apt.packages(
            packages=["apt-transport-https", "ca-certificates"],
            update=True,
        )

        yield from apt.key("https://syncthing.net/release-key.gpg")

        yield from apt.repo(
            src="deb [] https://apt.syncthing.net/ syncthing stable",
            filename="syncthing",
        )

        yield from apt.packages(
            packages=["syncthing"],
            update=True,
        )
    elif host.get_fact(PacmanPackages):
        yield from pacman.packages(["syncthing"], update=True)
    else:
        raise DeployError(
            f"Neither apt nor pacman were found. Cannot install syncthing."
        )


@operation
def enable(username=None, create_user=True):
    """Enables syncthing for the given user"""

    if not username:
        username = host.get_fact(User)
    else:
        users = host.get_fact(Users)
        if username not in users and create_user:
            yield from server.user(username, system=True, ensure_home=True)

    yield from systemd.service(f"syncthing@{username}", running=True, enabled=True)


@operation
def request(
    endpoint: str,
    method: str = "GET",
    data: dict = None,
    config: SyncthingConfig = None,
    base_url: str | None = None,
    api_key: str | None = None,
):
    yield create_request_curl_command(endpoint, method, data, config, base_url, api_key)


def get_folder_id(folder: dict):
    folder_id = folder.get("id")
    if folder_id is None:
        raise DeployError("Syncthing folder must have an id")
    return folder_id


@operation
def update_folder(
    partial_folder: dict,
    config: SyncthingConfig = None,
    base_url: str | None = None,
    api_key: str | None = None,
):
    folder_id = get_folder_id(partial_folder)
    yield from request(
        f"config/folders/{folder_id}",
        "PATCH",
        partial_folder,
        config,
        base_url,
        api_key,
    )


@operation
def add_folder(
    folder: dict,
    config: SyncthingConfig = None,
    base_url: str | None = None,
    api_key: str | None = None,
):
    folder_id = get_folder_id(folder)
    yield from request(
        f"config/folders/{folder_id}",
        "PUT",
        folder,
        config,
        base_url,
        api_key,
    )


@operation
def folder(
    folder: dict,
    config: SyncthingConfig = None,
    base_url: str | None = None,
    api_key: str | None = None,
):
    folder_id = get_folder_id(folder)
    # This is a race condition (folder can be created between the next two lines)
    existing_folder = host.get_fact(facts.Folder, folder_id, config, base_url, api_key)
    if existing_folder is None:
        yield from add_folder(folder, config, base_url, api_key)
    else:
        yield from update_folder(folder, config, base_url, api_key)


def get_device_id(device: dict):
    device_id = device.get("deviceID")
    if device_id is None:
        raise DeployError("Syncthing device must have an id")
    return device_id


@operation
def update_device(
    partial_device: dict,
    config: SyncthingConfig = None,
    base_url: str | None = None,
    api_key: str | None = None,
):
    device_id = get_device_id(partial_device)
    yield from request(
        f"config/devices/{device_id}",
        "PATCH",
        partial_device,
        config,
        base_url,
        api_key,
    )


@operation
def add_device(
    device: dict,
    config: SyncthingConfig = None,
    base_url: str | None = None,
    api_key: str | None = None,
):
    device_id = get_device_id(device)
    yield from request(
        f"config/devices/{device_id}",
        "PUT",
        device,
        config,
        base_url,
        api_key,
    )


@operation
def device(
    device: dict,
    config: SyncthingConfig = None,
    base_url: str | None = None,
    api_key: str | None = None,
):
    device_id = get_device_id(device)
    # This is a race condition (device can be created between the next two lines)
    existing_device = host.get_fact(facts.Device, device_id, config, base_url, api_key)
    if existing_device is None:
        yield from add_device(device, config, base_url, api_key)
    else:
        yield from update_device(device, config, base_url, api_key)
