import json
from pyinfra.api import FactBase, DeployError

from .common import SyncthingConfig, create_request_curl_command

ROOT_TAG = "configuration"
RELATIVE_CONFIG_PATH = ".config/syncthing"


class Config(FactBase):
    def command(self, username: str | None = None):
        username_command = username if username else "$(whoami)"
        return f"""
            HOME_DIR=$(getent passwd | cut -d: -f1,6 | grep {username_command}: | cut -d: -f2);
            syncthing cli --home "$HOME_DIR/{RELATIVE_CONFIG_PATH}" config dump-json
        """

    def process(self, output: list[str]):
        return SyncthingConfig(json.loads(" ".join(output)))


class RestFact(FactBase):
    not_found_ok: bool = False

    def command(
        self,
        endpoint: str,
        config: SyncthingConfig = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        non_error_status_codes = ["200"]
        if self.not_found_ok:
            non_error_status_codes.append("404")
        return create_request_curl_command(
            endpoint,
            config=config,
            base_url=base_url,
            api_key=api_key,
            non_error_status_codes=non_error_status_codes,
        )

    def process(self, output: list[str]):
        _, status_code, _ = output[0].rstrip().split(" ", 2)

        if self.not_found_ok and status_code == "404":
            return None

        if status_code != "200":
            raise DeployError(f"Unexpected syncthing API status code: {status_code}")

        headers_end_i = next(i for i, l in enumerate(output) if len(l.strip()) == 0)
        body_lines = output[headers_end_i + 1 :]
        return json.loads(" ".join(body_lines))


class RestConfigObject(RestFact):
    not_found_ok = True
    rest_name_plural: str

    def command(
        self,
        object_id: str,
        config: SyncthingConfig = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        return super().command(
            f"config/{self.rest_name_plural}/{object_id}",
            config,
            base_url,
            api_key,
        )


class Folder(RestConfigObject):
    rest_name_plural = "folders"


class Device(RestConfigObject):
    rest_name_plural = "devices"


class SystemStatus(RestFact):
    def command(
        self,
        config: SyncthingConfig = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        return super().command(
            f"system/status",
            config,
            base_url,
            api_key,
        )
