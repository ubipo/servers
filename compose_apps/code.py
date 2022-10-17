# Code server https://hub.docker.com/r/codercom/code-server

from pathlib import PosixPath
from compose_apps.create_app import create_app

create_app(
    "code",
    "codercom/code-server",
    [
        (PosixPath("test"), "/home/coder/project"),
        (PosixPath("config"), "/home/coder/.config"),
    ],
    [(8080, 8080)],
)
