from pyinfra.operations import server, files
from pyinfra import host
from libdeploys import cloud_init
import warnings


CLOUD_CONFIG_PATH = "/etc/cloud/cloud.cfg"
CLOUD_INIT_DISABLE_PATH = "/etc/cloud/cloud-init.disabled"

hostname = host.name
fqdn = host.data.get("fqdn")

if fqdn is None:
    raise Exception("No fqdn set for host")

cloud_init_enabled = host.get_fact(cloud_init.Status)
if cloud_init_enabled == cloud_init.StatusValue.DONE:
    warnings.warn(f"Disabling cloud-init on {host.name}")
    files.file(
        CLOUD_INIT_DISABLE_PATH,
        touch=True,
        present=True,
    )

server.hostname(hostname=hostname)

files.line(
    "/etc/hosts",
    line=f"127.0.0.1 {hostname} {fqdn}",
)
