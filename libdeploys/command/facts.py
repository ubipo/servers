from pyinfra.api import FactBase


class Exists(FactBase):
    def command(self, command: str):
        return f"command -v '{command}'"

    def process(self, output: list[str]):
        return len(output) > 0
