import json
from pyinfra.api import FactBase

from libdeploys.zabbix.common import create_api_call_command, ApiCredentials


class ApiFact(FactBase):
    def command(
        self,
        credentials: ApiCredentials,
        endpoint: str,
        parameters: dict,
    ):
        return create_api_call_command(credentials, endpoint, parameters)

    def process(self, output: list[str]):
        return json.loads(" ".join(output))


class User(ApiFact):
    def command(
        self,
        credentials: ApiCredentials,
        username: str,
    ):
        return super().command(
            credentials,
            "user.get",
            {
                "output": "extend",
                "filter": {
                    "username": username,
                },
            },
        )

    def process(self, output: list[str]):
        users = super().process(output)
        return users[0] if len(users) > 0 else None
