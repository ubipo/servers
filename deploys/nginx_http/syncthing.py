from io import StringIO
from util.nginx import create_nginx_config
from pyinfra.operations import files, server
from pyinfra import host, inventory

from libdeploys import syncthing
from nginx_http.tls_pfiers_wildcard.consts import *


AUTH_LOCATION = "/_auth"
AUTH_PROXY_BASE = "https://id.pfiers.net"

if "nginx_http_upstream_hosts" in host.groups:
    is_upstream = True
elif "nginx_http_proxy_hosts" in host.groups:
    is_upstream = False
else:
    raise RuntimeError(
        "Host is neither in nginx_http_upstream_hosts nor .._proxy_hosts"
    )

upstream_host = inventory.get_group("nginx_http_upstream_hosts")[0]
proxy_host = inventory.get_group("nginx_http_proxy_hosts")[0]
upstream_address = upstream_host.data.get("wg_ipv6_address")
proxy_address = proxy_host.data.get("wg_ipv6_address")

if is_upstream:
    syncthing_config = host.get_fact(Config, "syncthing")
    upstream_url = syncthing_config.base_url
else:
    upstream_url = f"https://[{upstream_address}]"

location_directives = [
    ("satisfy", "all"),
    ("allow", "fd61:1b78:37c8::1"),
    ("allow", "fd61:1b78:37c8::2"),
    ("allow", "2a01:4f8:1c1e:ec76::1"),
    ("allow", "109.131.226.50"),
    ("allow", "127.0.0.0/8"),
    ("deny", "all"),
]

if is_upstream:
    location_directives.append(("auth_request", AUTH_LOCATION))

location_directives.extend(
    [
        ("proxy_pass", upstream_url),
        ("set", "$proxy_header_real_ip $remote_addr"),
        ("set", "$proxy_header_forwarded_for $proxy_add_x_forwarded_for"),
        ("set", "$proxy_header_forwarded_proto $scheme"),
    ]
)

# Needs to be "localhost" because that's what syncthing is listening on and I
# don't want to change that (needs to still be accessible from localhost like
# normal).
# Alternative solution is to use the gui.insecureSkipHostcheck option.
# See: https://docs.syncthing.net/users/faq.html#why-do-i-get-host-check-error-in-the-gui-api
proxy_host_header = "localhost" if is_upstream else "$host"
location_directives.append(("proxy_set_header", f"Host {proxy_host_header}"))

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

if is_upstream:
    location_directives.extend(
        [
            ("add_header", "Set-Cookie $subrequest_auth_set_cookie"),
            (
                "auth_request_set",
                "$subrequest_auth_set_cookie $upstream_http_set_cookie",
            ),
        ]
    )
    subrequest_auth_locations = [
        (
            "location",
            f"= {AUTH_LOCATION}",
            [
                ("rewrite", ".* /subrequest-auth break"),
                ("proxy_pass", AUTH_PROXY_BASE),
                ("proxy_pass_request_body", False),
                ("proxy_set_header", 'Content-Length ""'),
                ("proxy_set_header", "X-Original-Host $http_host"),
                ("proxy_set_header", "X-Original-URI $request_uri"),
                (
                    "auth_request_set",
                    "$subrequest_auth_set_cookie $upstream_http_set_cookie",
                ),
            ],
        ),
        ("error_page", "401 = @error401"),
        (
            "location",
            "@error401",
            [
                (
                    "return",
                    f"302 {AUTH_PROXY_BASE}/consent?san=$scheme://$http_host$request_uri",
                ),
            ],
        ),
    ]
else:
    subrequest_auth_locations = []


server_config = create_nginx_config(
    (
        "server",
        "",
        [
            ("server_name", "syncthing.pfiers.net"),
            ("include", SNIPPET_VHOST_PATH),
            (
                "location",
                "/",
                location_directives,
            ),
            *subrequest_auth_locations,
        ],
    )
)
files.put(StringIO(server_config), str(SITES_DIR / "syncthing.conf"))

server.systemd.service("nginx", running=True, reloaded=True)
