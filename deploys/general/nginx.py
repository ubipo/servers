from io import StringIO
from pyinfra import host
from pyinfra.operations import apt, pacman, systemd, server, files
from pyinfra.facts import server as server_facts

from util.nginx import create_nginx_config

dist = host.get_fact(server_facts.LinuxDistribution)
dist_id = dist["release_meta"]["ID"]

if dist_id == "debian":
    apt.packages(["nginx"], update=True)
elif dist_id == "arch":
    pacman.packages(["nginx"], update=True)

server.user("nginx", system=True)

directives = [
    ("user", "nginx"),
    ("worker_processes", "auto"),
    ("events", ("", [("worker_connections", 1024)])),
    (
        "http",
        "",
        [
            ("sendfile", "on"),
            ("tcp_nopush", "on"),
            ("types_hash_max_size", 4096),
            ("keepalive_timeout", 65),
            ("gzip", "on"),
            ("include", "/etc/nginx/mime.types"),
            ("default_type", "application/octet-stream"),
            (
                "log_format",
                """main '$http_x_forwarded_for - $remote_user [$time_local] "$host" "$request" '
                '$status $body_bytes_sent "$http_referer" '
                '"$http_user_agent" $request_time'""",
            ),
            ("access_log", "/var/log/nginx/access.log main"),
            ("error_log", "/var/log/nginx/error.log"),
            ("include", "/etc/nginx/sites/*"),
        ],
    ),
]

if dist_id == "debian":
    directives.append(("pid", "/run/nginx.pid"))

config = create_nginx_config(*directives)
files.put(StringIO(config), "/etc/nginx/nginx.conf")

systemd.service("nginx", running=True, enabled=True)
