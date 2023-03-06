from pyinfra import inventory, host
from pyinfra.operations import server
from pathlib import PosixPath
from deploys.data.tijmid import *
import libdeploys.compose_app as compose_app
from deploys.data.app_ports import AppPorts
from util.compose import ComposeService
import secrets, string


def generate_alphanumerical(length: int):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for i in range(length))


OIDC_CLIENT_NAME = "Nextcloud"
CONTAINER_NAME = "nextcloud"
OCC_BASE_COMMAND = (
    f"docker container exec -u www-data {CONTAINER_NAME} php /var/www/html/occ"
)

# with closing(secretstorage.dbus_init()) as conn:
#     collection = secretstorage.get_default_collection(conn)
#     items = collection.search_items({"application": "myapp"})


def run():
    compose_app.create_compose_app(
        "nextcloud",
        [
            ComposeService(
                name=CONTAINER_NAME,
                image="nextcloud",
                volumes=[
                    (PosixPath("data"), "/var/www/html"),
                ],
                port_pairs=[(AppPorts.nextcloud.value, 80)],
            )
        ],
    )

    # Wait until OCC (OwnCloud Config) is available (container boot)
    server.shell(f"while {OCC_BASE_COMMAND}; [ $? -eq 255 ]; do sleep 1; done")

    # Install
    admin_password = generate_alphanumerical(16)
    server.shell(
        f"{OCC_BASE_COMMAND} maintenance:install --admin-pass {admin_password} && sleep 0.5"
    )

    # Change config
    server.shell(
        f"{OCC_BASE_COMMAND} config:system:set trusted_domains 0 --value cloud.pfiers.net"
    )
    # Set docker net as trusted proxy
    server.shell(
        f"{OCC_BASE_COMMAND} config:system:set trusted_proxies 0 --value '172.17.0.0/16'"
    )
    server.shell(
        f"{OCC_BASE_COMMAND} config:system:set overwriteprotocol --value https"
    )
    server.shell(f"{OCC_BASE_COMMAND} config:system:set skeletondirectory --value ''")

    # OIDC config
    server.shell(f"{OCC_BASE_COMMAND} app:install user_oidc")
    client_id = generate_alphanumerical(16)
    client_secret = generate_alphanumerical(24)
    server.shell(
        f"""{OCC_BASE_COMMAND} user_oidc:provider id-pfiers \
        '--clientid={client_id}' '--clientsecret={client_secret}' \
        '--discoveryuri=https://id.pfiers.net/.well-known/openid-configuration' \
        '--unique-uid=0'
    """
    )
    server.shell(
        f"{OCC_BASE_COMMAND} config:app:set --value=0 user_oidc allow_multiple_user_backends"
    )

    # Add Nextcloud to OIDC provider
    server.shell(
        f"{TIJMID_CLI} client --db {TIJMID_DB_PATH} delete --by-name '{OIDC_CLIENT_NAME}'"
    )
    server.shell(
        f"""{TIJMID_CLI} client --db '{TIJMID_DB_PATH}' create \
            --name '{OIDC_CLIENT_NAME}' \
            --id '{client_id}' \
            --secret '{client_secret}' \
            --redirect-uris 'https://cloud.pfiers.net/apps/user_oidc/code' \
            --post-logout-redirect-uris 'https://cloud.pfiers.net' \
            --require-pkce false
    """
    )

    # Contacts app
    server.shell(f"{OCC_BASE_COMMAND} app:install contacts")


app_hosts = inventory.get_group("app_hosts")
if host not in app_hosts:
    print(f"Skipping nextcloud deploy on {host.name} because it is not an app host")
else:
    run()
