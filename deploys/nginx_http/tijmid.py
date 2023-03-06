from io import StringIO
from util.nginx import create_nginx_config
from pyinfra.operations import files, server
from pyinfra import host, inventory

from nginx_http.tls_pfiers_wildcard.consts import *
from deploys.data.tijmid import *


if "nginx_http_upstream_hosts" in host.groups:
    is_upstream = True
elif "nginx_http_proxy_hosts" in host.groups:
    is_upstream = False
else:
    raise RuntimeError("Host is neither a tls_pfiers_wildcard leader nor follower")

upstream_host = inventory.get_group("nginx_http_upstream_hosts")[0]
proxy_host = inventory.get_group("nginx_http_proxy_hosts")[0]
upstream_address = upstream_host.data.get("wg_ipv6_address")
proxy_address = proxy_host.data.get("wg_ipv6_address")
upstream_url = (
    f"http://unix:{TIJMID_RUN_DIR / 'sock'}:"
    if is_upstream
    else f"https://[{upstream_address}]"
)

location_directives = [
    ("proxy_set_header", "Host $host"),
    ("proxy_pass", upstream_url),
    ("set", "$proxy_header_real_ip $remote_addr"),
    ("set", "$proxy_header_forwarded_for $proxy_add_x_forwarded_for"),
    ("set", "$proxy_header_forwarded_proto $scheme"),
]

if is_upstream:
    location_directives.extend(
        [
            (
                "if",
                f"($remote_addr = {proxy_address})",
                [
                    ("set", "$proxy_header_real_ip $http_x_real_ip"),
                    ("set", "$proxy_header_forwarded_for $http_x_forwarded_for"),
                    ("set", "$proxy_header_forwarded_proto $http_x_forwarded_proto"),
                ],
            ),
        ]
    )

location_directives.extend(
    [
        ("proxy_set_header", "X-Real-IP $proxy_header_real_ip"),
        ("proxy_set_header", "X-Forwarded-For $proxy_header_forwarded_for"),
        ("proxy_set_header", "X-Forwarded-Proto $proxy_header_forwarded_proto"),
    ]
)

server_config = create_nginx_config(
    (
        "server",
        "",
        [
            ("server_name", "id.pfiers.net"),
            ("include", SNIPPET_VHOST_PATH),
            (
                "location",
                "/",
                location_directives,
            ),
        ],
    )
)
files.put(StringIO(server_config), str(SITES_DIR / "id.conf"))

server.systemd.service("nginx", running=True, reloaded=True)
