from io import StringIO
from util.nginx import create_nginx_config
from pyinfra.operations import files, server

from nginx_http.tls_pfiers_wildcard.consts import *


server_config = create_nginx_config(
    (
        "server",
        "",
        [
            ("server_name", "_"),
            ("include", SNIPPET_VHOST_PATH),
            (
                "location",
                "/",
                [
                    ("default_type", "text/plain"),
                    ("return", "404 'Domain not found'"),
                ],
            ),
        ],
    )
)
files.put(StringIO(server_config), str(SITES_DIR / "fallback.conf"))

server.systemd.service("nginx", running=True, reloaded=True)
