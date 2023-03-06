# Code server https://hub.docker.com/r/codercom/code-server

from pathlib import PosixPath
import libdeploys.compose_app as compose_app

compose_app.create_compose_app(
    "code",
    "codercom/code-server",
    [
        (PosixPath("test"), "/home/coder/project"),
        (PosixPath("config"), "/home/coder/.config"),
    ],
    [(8080, 8080)],
)
