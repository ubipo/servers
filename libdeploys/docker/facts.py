from pyinfra.api import FactBase


class IsFunctional(FactBase):
    def command(self):
        return f"docker run hello-world"

    def process(self, output: list[str]):
        return "Hello from Docker!" in "\n".join(output)


class Version(FactBase):
    def command(self):
        return f"docker version --format '{{{{.Server.Version}}}}'"

    def process(self, output: list[str]):
        return output[0]
