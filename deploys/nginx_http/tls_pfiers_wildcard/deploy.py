from pyinfra.operations import files
from pyinfra import host

from nginx_http.tls_pfiers_wildcard.renewal import (
    setup_leader_renewal,
    setup_follower_renewal,
)
from nginx_http.tls_pfiers_wildcard.syncthing import (
    setup_leader_syncthing,
    setup_follower_syncthing,
)
from nginx_http.tls_pfiers_wildcard.consts import *

if "tls_pfiers_wildcard_leader_hosts" in host.groups:
    files.directory(str(KEYS_DIR), mode=750, group="syncthing")
    setup_leader_renewal()
    setup_leader_syncthing()
elif "tls_pfiers_wildcard_follower_hosts" in host.groups:
    files.directory(str(KEYS_DIR), mode=770, group="syncthing")
    setup_follower_renewal()
    setup_follower_syncthing()
else:
    raise RuntimeError("Host is not in a tls_pfiers_wildcard group")
