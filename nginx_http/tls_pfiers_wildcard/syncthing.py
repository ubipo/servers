from pyinfra import host, inventory
from pyinfra.api import DeployError

from deploys.syncthing.common import SyncthingConfig
import deploys.syncthing.operations as syncthing
from deploys.syncthing.facts import Config, SystemStatus

from nginx_http.tls_pfiers_wildcard.consts import *


def get_host_device_id(pyinfra_host):
    config = pyinfra_host.get_fact(Config, "syncthing")
    device_id = pyinfra_host.get_fact(SystemStatus, config)["myID"]
    return device_id


def setup_leader_syncthing():
    config: SyncthingConfig = host.get_fact(Config, "syncthing")
    syncthing.folder(
        {"id": SYNCTHING_FOLDER_ID, "path": str(KEYS_DIR), "type": "sendonly"},
        config=config,
    )

    followers = inventory.get_group("tls_pfiers_wildcard_follower_hosts")
    follower_ids = [get_host_device_id(follower) for follower in followers]
    print(f"{follower_ids=}")

    for follower_id in follower_ids:
        syncthing.add_device({"deviceID": follower_id}, config=config)

    follower_devices = [{"deviceID": follower_id} for follower_id in follower_ids]
    syncthing.update_folder(
        {"id": SYNCTHING_FOLDER_ID, "devices": follower_devices}, config=config
    )


def setup_follower_syncthing():
    config: SyncthingConfig = host.get_fact(Config, "syncthing")
    syncthing.folder(
        {"id": SYNCTHING_FOLDER_ID, "path": str(KEYS_DIR), "type": "receiveonly"},
        config=config,
    )

    leaders = iter(inventory.get_group("tls_pfiers_wildcard_leader_hosts"))
    leader = next(leaders, None)

    if leader is None:
        raise DeployError("No leader found")

    if next(leaders, None) != None:
        raise DeployError("More than one leader found")

    leader_id = get_host_device_id(leader)
    print(f"{leader_id=}")

    syncthing.add_device({"deviceID": leader_id}, config=config)
    syncthing.update_folder(
        {
            "id": SYNCTHING_FOLDER_ID,
            "devices": [
                {"deviceID": leader_id},
            ],
        },
        config=config,
    )
