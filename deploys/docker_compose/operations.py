from pathlib import PosixPath
from pyinfra.api import operation


@operation
def up(compose_file: PosixPath):
    yield f"cd {compose_file.parent} && docker compose up -d"
