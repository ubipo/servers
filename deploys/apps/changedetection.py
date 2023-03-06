from pathlib import PosixPath
import libdeploys.compose_app as compose_app
from util.compose import ComposeService


compose_app.create_compose_app(
    "changedetection",
    [
        ComposeService(
            name="changedetection",
            image="ghcr.io/dgtlmoon/changedetection.io",
            volumes=[
                (PosixPath("data"), "/datastore"),
            ],
            port_pairs=[(8060, 5000)],
            environment={
                "PLAYWRIGHT_DRIVER_URL": "ws://browserless:3000",
            },
        ),
        ComposeService(
            name="browserless",
            image="browserless/chrome",
            volumes=[
                (PosixPath("data"), "/datastore"),
            ],
            environment={
                "DEFAULT_LAUNCH_ARGS": "[--window-size=1920,1080]",
            },
        ),
    ],
)
